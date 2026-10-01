"""서울 ASOS 시간자료를 연도별 CSV로 내려받는다.

실행: python scripts/download_asos_hourly.py [시작연도] [끝연도]
      (기본 1996 ~ 2025, 이미 받은 연도는 건너뛴다)
"""
import sys
import time

import pandas as pd

from first_snow.config import DATA_DIR, STATION_ID
from first_snow.kma import asos_hourly, load_api_key

OUT_DIR = DATA_DIR / "hourly"


def download_year(year, api_key):
    months = []
    for month in range(1, 13):
        start = pd.Timestamp(year=year, month=month, day=1)
        end = start + pd.offsets.MonthEnd(0)
        months.append(asos_hourly(start, end, api_key=api_key))
        time.sleep(0.2)   # 서버에 부담을 주지 않도록 잠깐 쉰다
    return pd.concat(months, ignore_index=True)


def main():
    first = int(sys.argv[1]) if len(sys.argv) > 1 else 1996
    last = int(sys.argv[2]) if len(sys.argv) > 2 else 2025
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    api_key = load_api_key()

    for year in range(first, last + 1):
        path = OUT_DIR / f"asos_hourly_{STATION_ID}_{year}.csv"
        if path.exists():
            print(f"{year}: 이미 있음, 건너뜀")
            continue
        df = download_year(year, api_key)
        df.to_csv(path, index=False, encoding="utf-8-sig")
        print(f"{year}: {len(df)}시간 저장", flush=True)


if __name__ == "__main__":
    main()
