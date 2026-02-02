"""
export_devices.py
- .env에서 DATABASE_URL을 읽어서 Postgres(iotcoss) 접속
- public.devices 테이블에서 최근 N일 데이터 조회
- CSV 또는 JSON으로 내보내기

실행 예시)
  # 기본: 최근 7일치 -> devices.csv
  python export_devices.py

  # 최근 3일치 -> devices_3d.csv
  python export_devices.py --days 3 --out devices_3d.csv

  # 특정 MAC만
  python export_devices.py --days 7 --device-mac "F4:12:FA:9B:62:48" --out charger.csv

  # JSON으로
  python export_devices.py --days 7 --out devices.json
"""

import argparse
import asyncio
import os
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


def load_env() -> Path | None:
    """
    실행 위치(CWD)가 어디든 .env를 찾기 위해:
    1) 이 파일과 같은 폴더
    2) 상위 폴더들(몇 단계)
    순서로 .env를 탐색해서 로드
    """
    here = Path(__file__).resolve().parent

    candidates = [
        here / ".env",
        here.parent / ".env",
        here.parent.parent / ".env",
        here.parent.parent.parent / ".env",
    ]

    for p in candidates:
        if p.exists():
            load_dotenv(dotenv_path=p, override=False)
            return p

    return None


def get_database_url() -> str:
    env_path = load_env()
    db_url = os.getenv("DATABASE_URL")

    if not db_url:
        hint = f".env found at: {env_path}" if env_path else ".env not found"
        raise SystemExit(
            "❌ DATABASE_URL이 비어있습니다.\n"
            "1) .env 파일에 DATABASE_URL=postgresql+asyncpg://... 가 있는지 확인하고\n"
            "2) export_devices.py 기준 상위/동일 폴더 어디엔가 .env가 존재해야 합니다.\n"
            f"   ({hint})"
        )

    return db_url


async def fetch_devices(days: int = 7, limit: int = 0, device_mac: str | None = None) -> pd.DataFrame:
    db_url = get_database_url()

    engine = create_async_engine(
        db_url,
        echo=False,
        pool_pre_ping=True,
    )
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    start_ts = datetime.now() - timedelta(days=days)

    sql = """
    SELECT
        id,
        device_name,
        device_mac,
        temperature,
        humidity,
        energy_amp,
        relay_status,
        "timestamp"
    FROM public.devices
    WHERE "timestamp" >= :start_ts
    """

    params: dict = {"start_ts": start_ts}

    if device_mac:
        sql += " AND device_mac = :device_mac"
        params["device_mac"] = device_mac

    sql += ' ORDER BY "timestamp" ASC'

    if limit and limit > 0:
        sql += " LIMIT :limit"
        params["limit"] = limit

    async with SessionLocal() as session:
        result = await session.execute(text(sql), params)
        rows = result.fetchall()
        cols = result.keys()

    await engine.dispose()

    return pd.DataFrame(rows, columns=cols)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--days", type=int, default=7, help="최근 N일 데이터 조회")
    p.add_argument("--limit", type=int, default=0, help="0이면 제한 없음")
    p.add_argument("--device-mac", type=str, default=None, help="특정 device_mac만 필터")
    p.add_argument("--out", type=str, default="devices.csv", help="저장 파일명(.csv/.json)")
    return p.parse_args()


async def main():
    args = parse_args()

    df = await fetch_devices(days=args.days, limit=args.limit, device_mac=args.device_mac)

    out_lower = args.out.lower()
    if out_lower.endswith(".json"):
        df.to_json(args.out, orient="records", force_ascii=False, date_format="iso")
    else:
        # 엑셀/윈도우에서 한글 깨짐 방지: utf-8-sig
        df.to_csv(args.out, index=False, encoding="utf-8-sig")

    print(f"✅ exported rows: {len(df)} -> {args.out}")
    if len(df) > 0:
        print(df.head(5).to_string(index=False))


if __name__ == "__main__":
    asyncio.run(main())
