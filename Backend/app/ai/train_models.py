# train_models.py
import asyncio
import json
import os
from pathlib import Path
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from dotenv import load_dotenv

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text


def load_env() -> Path | None:
    """
    실행 위치가 어디든 .env를 잡기 위해:
    - 현재 파일 폴더
    - 상위 폴더들(최대 4단계)
    를 순회하며 탐색
    """
    here = Path(__file__).resolve().parent
    candidates = [
        here / ".env"
    ]

    for p in candidates:
        if p.exists():
            # override=True로 .env 값이 확실히 적용되게(환경변수 충돌 방지)
            load_dotenv(dotenv_path=p, override=True)
            return p
    return None


def get_db_url() -> str:
    env_path = load_env()
    db_url = os.getenv("DATABASE_URL")

    if not db_url:
        raise SystemExit(
            "❌ DATABASE_URL이 비어있음.\n"
            f"   - .env 위치: {env_path if env_path else '찾지 못함'}\n"
            "   - .env에 DATABASE_URL=postgresql+asyncpg://... 가 있는지 확인해."
        )
    return db_url


def otsu_threshold(values: np.ndarray, nbins: int = 128) -> float:
    """장비별 energy_amp 분포에서 STANDBY/LOAD 임계값 자동 추정(Otsu)."""
    values = values[np.isfinite(values)]
    if len(values) < 50:
        return float(np.nan)

    vmin, vmax = float(values.min()), float(values.max())
    if vmax <= vmin:
        return float(np.nan)

    hist, bin_edges = np.histogram(values, bins=nbins, range=(vmin, vmax))
    hist = hist.astype(np.float64)

    prob = hist / (hist.sum() + 1e-12)
    omega = np.cumsum(prob)
    mu = np.cumsum(prob * (bin_edges[:-1] + bin_edges[1:]) / 2.0)
    mu_t = mu[-1]

    sigma_b2 = (mu_t * omega - mu) ** 2 / (omega * (1.0 - omega) + 1e-12)
    idx = int(np.nanargmax(sigma_b2))
    thr = (bin_edges[idx] + bin_edges[idx + 1]) / 2.0
    return float(thr)


def robust_baseline(values: np.ndarray):
    """Median + MAD 기반 baseline(이상치 탐지용)."""
    values = values[np.isfinite(values)]
    if len(values) < 30:
        return None
    med = float(np.median(values))
    mad = float(np.median(np.abs(values - med)))
    return {"median": med, "mad": mad}


async def fetch_devices(days: int = 14) -> pd.DataFrame:
    db_url = get_db_url()
    start_ts = datetime.now() - timedelta(days=days)

    print(f"📌 fetch_devices() start | days={days} | start_ts={start_ts}", flush=True)

    # ✅ 연결/쿼리 타임아웃(멈춤 방지)
    # - timeout: 커넥션 타임아웃(초)
    # - command_timeout: 쿼리 실행 타임아웃(초)
    engine = create_async_engine(
        db_url,
        echo=False,
        pool_pre_ping=True,
        connect_args={"timeout": 10, "command_timeout": 60},
    )
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    sql = """
    SELECT device_mac, device_name, temperature, humidity, energy_amp, relay_status, "timestamp"
    FROM public.devices
    WHERE "timestamp" >= :start_ts
    ORDER BY "timestamp" ASC
    """

    try:
        async with SessionLocal() as session:
            res = await session.execute(text(sql), {"start_ts": start_ts})
            rows = res.fetchall()
            cols = res.keys()
    finally:
        await engine.dispose()

    df = pd.DataFrame(rows, columns=cols)
    print(f"✅ fetch_devices() done | rows={len(df)}", flush=True)
    return df


async def main():
    print("🚀 train_models.py start", flush=True)

    # 혹시라도 “중간에 멈춤”이면 여기서 걸림 → 로그로 확인 가능
    df = await fetch_devices(days=14)

    if df.empty:
        raise SystemExit("❌ 학습할 데이터가 없음(최근 14일).")

    print(f"📊 raw df shape = {df.shape}", flush=True)

    # 타입 정리
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["relay_status"] = df["relay_status"].astype(str).str.lower()

    thresholds = {}
    baselines = {}

    unique_devices = df["device_mac"].nunique(dropna=True)
    print(f"🔎 unique device_mac = {unique_devices}", flush=True)

    for mac, g in df.groupby("device_mac"):
        g_on = g[g["relay_status"] == "on"].copy()
        amps = g_on["energy_amp"].astype(float).to_numpy()

        thr = otsu_threshold(amps)
        if not np.isfinite(thr):
            thr = float(np.nanmedian(amps)) if len(amps) else 0.05

        device_name = str(g["device_name"].iloc[-1]) if len(g) else ""

        thresholds[mac] = {
            "device_name": device_name,
            "standby_load_threshold_amp": float(thr),
        }

        base = robust_baseline(amps)
        if base:
            baselines[mac] = {
                "device_name": device_name,
                "amp_median": base["median"],
                "amp_mad": base["mad"],
            }

    out_dir = Path(__file__).resolve().parent / "models"
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "thresholds.json").write_text(
        json.dumps(thresholds, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    (out_dir / "baselines.json").write_text(
        json.dumps(baselines, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"✅ saved thresholds: {out_dir / 'thresholds.json'} ({len(thresholds)} devices)", flush=True)
    print(f"✅ saved baselines : {out_dir / 'baselines.json'} ({len(baselines)} devices)", flush=True)
    print("🎉 train_models.py finished", flush=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        # 어떤 이유로든 “조용히 종료”하는 걸 막고, 에러를 확실히 보이게
        import traceback
        print("💥 ERROR 발생:", repr(e), flush=True)
        traceback.print_exc()
        raise
