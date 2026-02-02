"""
ai_server.py (Backend/app/ai 안에서만 독립 실행)

- .env의 DATABASE_URL로 Postgres 연결
- models/thresholds.json, models/baselines.json 로드
- public.devices 기반으로:
  1) 현재 상태(state) 분류: IDLE / STANDBY / LOAD
  2) 이상치 탐지(robust z-score)
  3) standby 전력낭비(Wh) 추정
  4) 리포트(요약 문장)

실행:
  cd Backend/app/ai
  python ai_server.py

테스트:
  http://127.0.0.1:8001/docs

추가:
- 시작 전에 8001 포트를 점유한 LISTENING 프로세스가 있으면 자동 종료(Windows)
  (.env에서 AI_KILL_PORT_ON_START=0 하면 끌 수 있음)
"""

import os
import json
import math
import time
import logging
import traceback
import platform
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

import numpy as np
import pandas as pd
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Query, Request
import uvicorn

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker


# -----------------------
# 0) 로깅 설정
# -----------------------
LOG_LEVEL = os.getenv("AI_LOG_LEVEL", "DEBUG").upper()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.DEBUG),
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("ai_server")


def mask_db_url(url: str) -> str:
    # 비번 마스킹용
    # postgresql+asyncpg://user:pass@host:5432/db -> user:***@host...
    try:
        if "://" not in url or "@" not in url:
            return "***"
        scheme, rest = url.split("://", 1)
        cred, after = rest.split("@", 1)
        if ":" in cred:
            user = cred.split(":", 1)[0]
            return f"{scheme}://{user}:***@{after}"
        return f"{scheme}://***@{after}"
    except Exception:
        return "***"


# -----------------------
# 0.5) 실행 포트 점유 프로세스 자동 종료 (Windows)
# -----------------------
AI_HOST = os.getenv("AI_HOST", "127.0.0.1")
AI_PORT = int(os.getenv("AI_PORT", "8001"))
AI_KILL_PORT_ON_START = os.getenv("AI_KILL_PORT_ON_START", "1") == "1"


def _kill_listening_pids_windows(port: int) -> List[int]:
    """
    Windows: netstat로 LISTENING pid 찾고 taskkill로 종료
    """
    try:
        out = subprocess.check_output(
            ["netstat", "-ano", "-p", "tcp"],
            text=True,
            encoding="cp949",
            errors="ignore",
        )
    except Exception:
        out = subprocess.check_output(
            ["netstat", "-ano", "-p", "tcp"],
            text=True,
            errors="ignore",
        )

    pids = set()

    # 라인 예시:
    # TCP    127.0.0.1:8001   0.0.0.0:0   LISTENING   12345
    # TCP    [::1]:8001       [::]:0      LISTENING   12345
    for line in out.splitlines():
        if "LISTENING" not in line:
            continue
        if f":{port}" not in line:
            continue

        parts = line.split()
        if len(parts) < 5:
            continue

        local_addr = parts[1]
        state = parts[3]
        pid_str = parts[4]

        if state.upper() != "LISTENING":
            continue
        if not pid_str.isdigit():
            continue

        if local_addr.endswith(f":{port}"):
            pids.add(int(pid_str))

    killed: List[int] = []
    if not pids:
        return killed

    logger.warning(f"🟠 Port {port} in use. Trying to kill LISTENING pids={sorted(pids)}")

    for pid in sorted(pids):
        try:
            subprocess.check_call(
                ["taskkill", "/PID", str(pid), "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logger.warning(f"✅ killed pid={pid} (port={port})")
            killed.append(pid)
        except subprocess.CalledProcessError:
            logger.warning(f"❌ failed to kill pid={pid} (maybe no permission)")
        except Exception as e:
            logger.warning(f"❌ error killing pid={pid}: {e}")

    return killed


def kill_port_if_needed(host: str, port: int) -> None:
    """
    시작 전에 포트 점유 프로세스를 정리해주는 preflight.
    """
    if not AI_KILL_PORT_ON_START:
        logger.info("AI_KILL_PORT_ON_START=0 → port kill preflight skipped.")
        return

    if platform.system().lower() == "windows":
        killed = _kill_listening_pids_windows(port)
        if killed:
            # 죽인 직후 OS가 포트 해제하는 데 약간 텀 필요할 수 있음
            time.sleep(0.5)
        else:
            logger.info(f"🟢 Port {port} seems free (no LISTENING pid found).")
    else:
        logger.info(f"Non-Windows detected. Skip auto kill. (host={host}, port={port})")


# -----------------------
# 1) env 로드 (CWD 상관없이)
# -----------------------
def load_env() -> Path | None:
    here = Path(__file__).resolve().parent
    # Backend/app/ai -> Backend/app -> Backend 순으로 .env 탐색
    candidates = [
        here / ".env",  # Backend/app/ai/.env
        here.parent / ".env",  # Backend/app/.env
        here.parent.parent / ".env",  # Backend/.env
    ]
    for p in candidates:
        if p.exists():
            load_dotenv(dotenv_path=p, override=False)
            logger.info(f"✅ .env loaded from: {p}")
            return p
    logger.warning("⚠️ .env not found in any candidate path.")
    return None


ENV_PATH = load_env()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(f"DATABASE_URL 없음. .env 확인해. (found: {ENV_PATH})")

logger.info(f"✅ DATABASE_URL detected: {mask_db_url(DATABASE_URL)}")

DEFAULT_VOLTAGE = float(os.getenv("DEFAULT_VOLTAGE", "220"))
logger.info(f"✅ DEFAULT_VOLTAGE = {DEFAULT_VOLTAGE}")


# -----------------------
# 2) 모델 파일 로딩
# -----------------------
BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"
THR_PATH = MODELS_DIR / "thresholds.json"
BASELINE_PATH = MODELS_DIR / "baselines.json"

logger.info(f"📁 BASE_DIR   : {BASE_DIR}")
logger.info(f"📁 MODELS_DIR : {MODELS_DIR}")
logger.info(f"📄 thresholds.json exists? {THR_PATH.exists()} -> {THR_PATH}")
logger.info(f"📄 baselines.json exists?  {BASELINE_PATH.exists()} -> {BASELINE_PATH}")


class ModelStore:
    def __init__(self):
        self.thresholds: Dict[str, Dict[str, Any]] = {}
        self.baselines: Dict[str, Dict[str, Any]] = {}

    def load(self):
        logger.info("🔁 Loading models...")
        self.thresholds = {}
        self.baselines = {}

        if THR_PATH.exists():
            self.thresholds = json.loads(THR_PATH.read_text(encoding="utf-8"))
            logger.info(f"✅ thresholds loaded: {len(self.thresholds)} devices")
        else:
            logger.warning("⚠️ thresholds.json not found. fallback threshold will be used.")

        if BASELINE_PATH.exists():
            self.baselines = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
            logger.info(f"✅ baselines loaded: {len(self.baselines)} devices")
        else:
            logger.warning("⚠️ baselines.json not found. anomaly detection will return empty.")

    def get_threshold(self, mac: str, fallback: float = 0.05) -> float:
        item = self.thresholds.get(mac)
        if not item:
            return fallback
        return float(item.get("standby_load_threshold_amp", fallback))

    def get_baseline(self, mac: str) -> Optional[Dict[str, Any]]:
        return self.baselines.get(mac)


store = ModelStore()
store.load()


# -----------------------
# 3) DB 세션(독립 서버에서만 씀)
# -----------------------
logger.info("🔌 Creating async DB engine...")
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # SQLAlchemy가 자동 SQL 찍는 건 끔
    pool_pre_ping=True,
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
logger.info("✅ Engine created.")


async def fetch_recent_point(device_mac: str) -> Optional[Dict[str, Any]]:
    sql = """
    SELECT device_mac, device_name, relay_status, energy_amp, temperature, humidity, "timestamp"
    FROM public.devices
    WHERE device_mac = :mac
    ORDER BY "timestamp" DESC
    LIMIT 1
    """
    params = {"mac": device_mac}
    t0 = time.perf_counter()
    logger.debug(f"[DB] fetch_recent_point mac={device_mac}")
    try:
        async with SessionLocal() as session:
            res = await session.execute(text(sql), params)
            row = res.mappings().first()
        ms = (time.perf_counter() - t0) * 1000
        logger.debug(f"[DB] fetch_recent_point done ({ms:.1f}ms) found={row is not None}")
        return dict(row) if row else None
    except Exception as e:
        logger.error(f"[DB] fetch_recent_point error: {e}")
        logger.error(traceback.format_exc())
        raise


async def fetch_window(device_mac: str, hours: int = 24) -> pd.DataFrame:
    start_ts = datetime.now() - timedelta(hours=hours)
    sql = """
    SELECT device_mac, device_name, relay_status, energy_amp, temperature, humidity, "timestamp"
    FROM public.devices
    WHERE device_mac = :mac AND "timestamp" >= :start_ts
    ORDER BY "timestamp" ASC
    """
    params = {"mac": device_mac, "start_ts": start_ts}
    t0 = time.perf_counter()
    logger.debug(f"[DB] fetch_window mac={device_mac} hours={hours} start_ts={start_ts.isoformat()}")

    try:
        async with SessionLocal() as session:
            res = await session.execute(text(sql), params)
            rows = res.fetchall()
            cols = res.keys()
        ms = (time.perf_counter() - t0) * 1000
        logger.debug(f"[DB] fetch_window done ({ms:.1f}ms) rows={len(rows)}")
        return pd.DataFrame(rows, columns=cols)
    except Exception as e:
        logger.error(f"[DB] fetch_window error: {e}")
        logger.error(traceback.format_exc())
        raise


async def fetch_device_list(limit: int = 200) -> List[Dict[str, Any]]:
    sql = """
    SELECT DISTINCT ON (device_mac)
        device_mac,
        device_name
    FROM public.devices
    ORDER BY device_mac, "timestamp" DESC
    LIMIT :limit
    """
    params = {"limit": limit}
    t0 = time.perf_counter()
    logger.debug(f"[DB] fetch_device_list limit={limit}")

    try:
        async with SessionLocal() as session:
            res = await session.execute(text(sql), params)
            rows = res.mappings().all()
        ms = (time.perf_counter() - t0) * 1000
        logger.debug(f"[DB] fetch_device_list done ({ms:.1f}ms) rows={len(rows)}")
        return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"[DB] fetch_device_list error: {e}")
        logger.error(traceback.format_exc())
        raise


# -----------------------
# 4) AI 로직 (devices 테이블만)
# -----------------------
def classify_state(relay_status: str, amp: float, thr: float) -> str:
    rs = (relay_status or "").lower()
    if rs != "on":
        return "IDLE"
    return "STANDBY" if amp < thr else "LOAD"


def robust_zscore(x: float, median: float, mad: float) -> float:
    denom = (1.4826 * mad) if mad and mad > 1e-12 else 1e-12
    return (x - median) / denom


def detect_anomalies(df: pd.DataFrame, baseline: Optional[Dict[str, Any]], z_thr: float = 6.0):
    logger.debug(f"[AI] detect_anomalies start df_rows={len(df)} baseline={'yes' if baseline else 'no'} z_thr={z_thr}")
    if df.empty or not baseline:
        return []

    med = float(baseline.get("amp_median", 0.0))
    mad = float(baseline.get("amp_mad", 0.0))

    d = df.copy()
    d["timestamp"] = pd.to_datetime(d["timestamp"], errors="coerce")
    d["relay_status"] = d["relay_status"].astype(str).str.lower()
    d["energy_amp"] = pd.to_numeric(d["energy_amp"], errors="coerce").fillna(0.0)
    d = d.dropna(subset=["timestamp"])

    # on일 때만 검사
    d = d[d["relay_status"] == "on"]

    out = []
    for _, r in d.iterrows():
        amp = float(r["energy_amp"])
        z = robust_zscore(amp, med, mad)
        if abs(z) >= z_thr:
            out.append(
                {
                    "timestamp": r["timestamp"].isoformat(),
                    "energy_amp": amp,
                    "z": float(z),
                    "reason": f"amp_outlier_robust_z>={z_thr}",
                }
            )

    logger.debug(f"[AI] detect_anomalies done anomalies={len(out)} (median={med}, mad={mad})")
    return out


def compute_standby_wh(df: pd.DataFrame, thr: float, voltage: float = DEFAULT_VOLTAGE) -> float:
    logger.debug(f"[AI] compute_standby_wh start df_rows={len(df)} thr={thr} voltage={voltage}")
    if df.empty:
        return 0.0

    d = df.copy()
    d["timestamp"] = pd.to_datetime(d["timestamp"], errors="coerce")
    d = d.dropna(subset=["timestamp"]).sort_values("timestamp")

    d["relay_status"] = d["relay_status"].astype(str).str.lower()
    d["energy_amp"] = pd.to_numeric(d["energy_amp"], errors="coerce").fillna(0.0)

    d["state"] = np.where(
        d["relay_status"] != "on",
        "IDLE",
        np.where(d["energy_amp"] < thr, "STANDBY", "LOAD"),
    )

    dt = (d["timestamp"].shift(-1) - d["timestamp"]).dt.total_seconds().fillna(0).to_numpy()
    amps = d["energy_amp"].to_numpy()
    is_standby = (d["state"].to_numpy() == "STANDBY").astype(np.float64)

    wh = float(np.sum((voltage * amps) * (dt / 3600.0) * is_standby))
    if not math.isfinite(wh):
        logger.warning("[AI] compute_standby_wh got non-finite wh -> returning 0")
        return 0.0

    wh = max(0.0, wh)
    logger.debug(f"[AI] compute_standby_wh done standby_wh={wh:.4f}")
    return wh


# -----------------------
# 5) FastAPI (이 파일만 실행)
# -----------------------
app = FastAPI(title="IoTCOSS AI API (standalone)", version="0.1.0")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    t0 = time.perf_counter()
    logger.info(f"[REQ] {request.method} {request.url.path} query={dict(request.query_params)}")
    try:
        response = await call_next(request)
        ms = (time.perf_counter() - t0) * 1000
        logger.info(f"[RES] {request.method} {request.url.path} -> {response.status_code} ({ms:.1f}ms)")
        return response
    except Exception as e:
        ms = (time.perf_counter() - t0) * 1000
        logger.error(f"[ERR] {request.method} {request.url.path} ({ms:.1f}ms) error={e}")
        logger.error(traceback.format_exc())
        raise


@app.get("/health")
async def health():
    logger.debug("[API] /health")
    return {
        "ok": True,
        "env_path": str(ENV_PATH) if ENV_PATH else None,
        "models_dir": str(MODELS_DIR),
        "thresholds_loaded": len(store.thresholds),
        "baselines_loaded": len(store.baselines),
        "host": AI_HOST,
        "port": AI_PORT,
    }


@app.post("/models/reload")
async def reload_models():
    logger.debug("[API] /models/reload")
    store.load()
    return {"ok": True, "thresholds_loaded": len(store.thresholds), "baselines_loaded": len(store.baselines)}


@app.get("/devices")
async def list_devices(limit: int = Query(200, ge=1, le=2000)):
    logger.debug(f"[API] /devices limit={limit}")
    items = await fetch_device_list(limit=limit)
    return {"items": items, "limit": limit}


@app.get("/devices/{device_mac}/state")
async def get_state(device_mac: str):
    logger.debug(f"[API] /devices/{device_mac}/state")
    row = await fetch_recent_point(device_mac)
    if not row:
        raise HTTPException(status_code=404, detail="device_mac 데이터 없음 (public.devices)")

    thr = store.get_threshold(device_mac)
    amp = float(row.get("energy_amp") or 0.0)
    rs = str(row.get("relay_status") or "").lower()
    state = classify_state(rs, amp, thr)

    logger.debug(f"[AI] state computed mac={device_mac} rs={rs} amp={amp} thr={thr} -> {state}")

    return {
        "device_mac": device_mac,
        "device_name": row.get("device_name"),
        "timestamp": str(row.get("timestamp")),
        "relay_status": rs,
        "energy_amp": amp,
        "threshold_amp": thr,
        "state": state,
    }


@app.get("/devices/{device_mac}/anomalies")
async def get_anomalies(
    device_mac: str,
    hours: int = Query(24, ge=1, le=168),
    z_thr: float = Query(3.0, ge=2.0, le=20.0),
):
    logger.debug(f"[API] /devices/{device_mac}/anomalies hours={hours} z_thr={z_thr}")
    df = await fetch_window(device_mac, hours=hours)
    baseline = store.get_baseline(device_mac)
    items = detect_anomalies(df, baseline, z_thr=z_thr)

    return {
        "device_mac": device_mac,
        "hours": hours,
        "z_threshold": z_thr,
        "count": len(items),
        "items": items,
    }


@app.get("/devices/{device_mac}/waste")
async def get_waste(
    device_mac: str,
    hours: int = Query(24, ge=1, le=168),
    voltage: float = Query(DEFAULT_VOLTAGE, ge=100, le=260),
):
    logger.debug(f"[API] /devices/{device_mac}/waste hours={hours} voltage={voltage}")
    df = await fetch_window(device_mac, hours=hours)
    thr = store.get_threshold(device_mac)
    standby_wh = compute_standby_wh(df, thr, voltage=voltage)

    return {
        "device_mac": device_mac,
        "hours": hours,
        "voltage": float(voltage),
        "standby_wh": float(standby_wh),
    }


@app.get("/devices/{device_mac}/report")
async def get_report(
    device_mac: str,
    hours: int = Query(24, ge=1, le=168),
    voltage: float = Query(DEFAULT_VOLTAGE, ge=100, le=260),
):
    logger.debug(f"[API] /devices/{device_mac}/report hours={hours} voltage={voltage}")
    state_now = await get_state(device_mac)
    anomalies = await get_anomalies(device_mac, hours=hours, z_thr=3.0)
    waste = await get_waste(device_mac, hours=hours, voltage=voltage)

    summary = (
        f"최근 {hours}시간 기준 standby 추정 {waste['standby_wh']:.2f}Wh, "
        f"이상치 {anomalies['count']}건, 현재 상태 {state_now['state']}."
    )
    if waste["standby_wh"] >= 50:
        summary += " standby 낭비가 큰 편이라 미사용 시 차단을 권장."
    if anomalies["count"] >= 3:
        summary += " 이상치가 반복되어 센서/부하/릴레이 점검 권장."

    logger.info(f"[REPORT] mac={device_mac} -> {summary}")

    return {
        "device_mac": device_mac,
        "hours": hours,
        "state_now": state_now,
        "anomalies": anomalies,
        "waste": waste,
        "summary": summary,
    }


if __name__ == "__main__":
    # 이 파일만 단독 실행 (기존 백엔드 main이랑 전혀 무관)
    logger.info("🚀 Starting standalone AI server...")
    logger.info(f"📌 Open docs: http://{AI_HOST}:{AI_PORT}/docs")

    # ✅ 시작 전에 포트 점유 프로세스 정리 (Windows)
    kill_port_if_needed(AI_HOST, AI_PORT)

    uvicorn.run(app, host=AI_HOST, port=AI_PORT, reload=False, log_level="info")
