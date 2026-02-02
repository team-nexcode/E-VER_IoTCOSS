# train_profiles.py
"""
train_profiles.py
- dummy_devices.csv 같은 데이터로 "기기별 시간대 패턴" 학습
- 결과를 models/profiles.json 저장

사용 예)
  cd Backend/app/ai

  # CSV로 학습
  python train_profiles.py --input dummy_devices.csv --out models/profiles.json

  # 최근 N일 DB에서 가져와 학습 (DATABASE_URL 필요)
  python train_profiles.py --from-db --days 14 --out models/profiles.json
"""

import argparse
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


# -----------------------
# env 로드
# -----------------------
def load_env():
    here = Path(__file__).resolve().parent
    candidates = [here / ".env", here.parent / ".env"]
    for p in candidates:
        if p.exists():
            load_dotenv(p, override=False)
            return p
    return None


def get_db_url() -> str:
    load_env()
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise SystemExit("❌ DATABASE_URL이 비어있음. .env 확인해.")
    return db_url


# -----------------------
# 데이터 로딩
# -----------------------
def load_from_csv(csv_path: str) -> pd.DataFrame:
    p = Path(csv_path)
    if not p.exists():
        raise SystemExit(f"❌ CSV 파일 없음: {p}")

    df = pd.read_csv(p)

    # 필수 컬럼 체크 (없으면 여기서 바로 터뜨려서 원인 명확히)
    need = {"device_mac", "device_name", "relay_status", "energy_amp", "timestamp"}
    missing = need - set(df.columns)
    if missing:
        raise SystemExit(f"❌ CSV에 필요한 컬럼이 없음: {sorted(missing)}")

    return df


async def load_from_db(days: int = 14) -> pd.DataFrame:
    db_url = get_db_url()
    engine = create_async_engine(db_url, echo=False, pool_pre_ping=True)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    start_ts = datetime.now() - timedelta(days=days)
    sql = """
    SELECT device_mac, device_name, relay_status, energy_amp, temperature, humidity, "timestamp"
    FROM public.devices
    WHERE "timestamp" >= :start_ts
    ORDER BY "timestamp" ASC
    """

    async with SessionLocal() as session:
        res = await session.execute(text(sql), {"start_ts": start_ts})
        rows = res.fetchall()
        cols = res.keys()

    await engine.dispose()
    return pd.DataFrame(rows, columns=cols)


# -----------------------
# 핵심: 프로파일 생성
# -----------------------
def build_profiles(df: pd.DataFrame) -> dict:
    """
    각 device_mac별로
      - on_rate[dow][hour] : 그 시간대에 relay_status=on 비율
      - amp_median_on[dow][hour] : on일 때 energy_amp 중앙값
    을 저장.

    나중에 "평소 OFF인 시간대인데 지금 STANDBY로 오래 유지" 같은 판단 근거로 씀.
    """
    d = df.copy()

    d["timestamp"] = pd.to_datetime(d["timestamp"], errors="coerce")
    d = d.dropna(subset=["timestamp"])

    d["relay_status"] = d["relay_status"].astype(str).str.lower()
    d["energy_amp"] = pd.to_numeric(d["energy_amp"], errors="coerce").fillna(0.0)

    d["dow"] = d["timestamp"].dt.dayofweek  # 0=Mon ... 6=Sun
    d["hour"] = d["timestamp"].dt.hour

    profiles = {}

    for mac, g in d.groupby("device_mac"):
        device_name = str(g["device_name"].dropna().iloc[-1]) if len(g["device_name"].dropna()) else ""

        # 7x24 init
        on_rate = [[0.0 for _ in range(24)] for _ in range(7)]
        amp_median_on = [[0.0 for _ in range(24)] for _ in range(7)]
        sample_cnt = [[0 for _ in range(24)] for _ in range(7)]

        # 그룹핑(요일/시간대)
        for (dow, hour), gh in g.groupby(["dow", "hour"]):
            dow = int(dow)
            hour = int(hour)

            sample_cnt[dow][hour] = int(len(gh))
            on_mask = (gh["relay_status"] == "on")
            on_rate[dow][hour] = float(on_mask.mean()) if len(gh) else 0.0

            if on_mask.any():
                amps = gh.loc[on_mask, "energy_amp"].to_numpy(dtype=float)
                amp_median_on[dow][hour] = float(np.median(amps))
            else:
                amp_median_on[dow][hour] = 0.0

        profiles[mac] = {
            "device_name": device_name,
            "schema": "dow_hour_profile_v1",
            "generated_at": datetime.now().isoformat(),
            "on_rate": on_rate,
            "amp_median_on": amp_median_on,
            "sample_cnt": sample_cnt,
            # 추천에 쓰는 기본 정책값(원하면 나중에 기기별로 튜닝 가능)
            "policy": {
                "usually_off_onrate_lt": 0.20,      # 이보다 on_rate 낮으면 '평소 OFF 시간대'로 판단
                "standby_minutes_ge": 30,           # standby가 이 이상이면 의심
                "waste_wh_ge": 10.0,                # 낭비(Wh)가 이 이상이면 의심
            },
        }

    return profiles


def save_json(obj: dict, out_path: str):
    base = Path(__file__).resolve().parent  # train_profiles.py 폴더
    out = Path(out_path)
    if not out.is_absolute():
        out = base / out  # 상대경로면 base 기준으로 붙임

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ wrote: {out.resolve()}")



def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=str, default="dummy_devices.csv", help="CSV 입력 파일")
    p.add_argument("--out", type=str, default="models/profiles.json", help="저장 파일")
    p.add_argument("--from-db", action="store_true", help="DB에서 최근 데이터로 학습")
    p.add_argument("--days", type=int, default=14, help="DB 학습 시 최근 N일")
    return p.parse_args()


async def main():
    args = parse_args()

    if args.from_db:
        df = await load_from_db(days=args.days)
        src = f"DB(last {args.days} days)"
    else:
        df = load_from_csv(args.input)
        src = f"CSV({args.input})"

    if df.empty:
        raise SystemExit(f"❌ 학습할 데이터가 없음: {src}")

    profiles = build_profiles(df)
    save_json(profiles, args.out)

    print(f"✅ profiles saved -> {args.out}")
    print(f"   source: {src}")
    print(f"   devices: {len(profiles)}")
    # 샘플 하나 미리보기
    any_mac = next(iter(profiles.keys()))
    print(f"   sample mac: {any_mac} name={profiles[any_mac].get('device_name')}")
    print("✅ current working dir:", Path.cwd())



if __name__ == "__main__":
    asyncio.run(main())
