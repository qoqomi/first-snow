"""기상청 공공데이터포털 API 클라이언트."""
import os
import time
from datetime import datetime, timedelta, timezone

import pandas as pd
import requests

from .config import ROOT, SEOUL_GRID, STATION_ID

ASOS_HOURLY_URL = "https://apis.data.go.kr/1360000/AsosHourlyInfoService/getWthrDataList"
VILAGE_FCST_URL = "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"

KST = timezone(timedelta(hours=9))

# 단기예보 발표 시각 (하루 8번). 발표 후 약 10분 뒤부터 API로 받을 수 있다.
FORECAST_BASE_HOURS = [2, 5, 8, 11, 14, 17, 20, 23]


def load_api_key():
    """환경변수 KMA_API_KEY 또는 프로젝트 루트의 .env에서 인증키를 읽는다."""
    key = os.environ.get("KMA_API_KEY")
    if key:
        return key.strip()

    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("KMA_API_KEY="):
                key = line.split("=", 1)[1].strip()
                if key:
                    return key
    raise RuntimeError("KMA_API_KEY가 없습니다. .env 파일에 KMA_API_KEY=인증키 를 넣어 주세요.")


def _get(url, params, retries=5):
    """API를 호출해서 item 목록을 돌려준다. 일시적인 오류는 간격을 늘려가며 다시 시도한다."""
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, timeout=30)
            r.raise_for_status()
            body = r.json()["response"]
            code = body["header"]["resultCode"]
            if code == "03":            # NODATA_ERROR: 해당 기간 자료 없음
                return []
            if code != "00":
                raise RuntimeError(f"API 오류 {code}: {body['header']['resultMsg']}")
            return body["body"]["items"]["item"]
        except (requests.RequestException, ValueError, KeyError) as e:
            if attempt == retries - 1:
                # 요청 URL에 인증키가 들어 있으므로 원래 예외 메시지에서 키를 지우고,
                # 키가 담긴 원래 예외는 연결하지 않는다 (로그에 키가 남지 않도록).
                message = str(e).replace(params.get("serviceKey", ""), "<KEY>")
                raise RuntimeError(f"API 호출 실패 ({type(e).__name__}): {message}") from None
            time.sleep(5 * 2 ** attempt)   # 5, 10, 20, 40초


def asos_hourly(start, end, station=STATION_ID, api_key=None):
    """ASOS 시간자료를 받아 DataFrame으로 돌려준다.

    start, end : 'YYYY-MM-DD' (end 포함). 한 번에 최대 999시간이므로 40일 이내로 호출한다.
    """
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    params = {
        "serviceKey": api_key or load_api_key(),
        "pageNo": 1,
        "numOfRows": 999,
        "dataType": "JSON",
        "dataCd": "ASOS",
        "dateCd": "HR",
        "startDt": start.strftime("%Y%m%d"),
        "startHh": "00",
        "endDt": end.strftime("%Y%m%d"),
        "endHh": "23",
        "stnIds": str(station),
    }
    items = _get(ASOS_HOURLY_URL, params)
    return pd.DataFrame(items)


def latest_base_time(now=None):
    """지금 받을 수 있는 가장 최근 단기예보 발표 시각 (KST)."""
    now = (now or datetime.now(KST)) - timedelta(minutes=15)
    for hour in reversed(FORECAST_BASE_HOURS):
        if now.hour >= hour:
            return now.replace(hour=hour, minute=0, second=0, microsecond=0)
    # 오늘 02시 발표 전이면 어제 23시 발표를 쓴다
    return (now - timedelta(days=1)).replace(hour=23, minute=0, second=0, microsecond=0)


def vilage_forecast(base=None, grid=SEOUL_GRID, api_key=None):
    """단기예보(약 3일, 1시간 단위)를 받아 시각별 표로 돌려준다.

    반환 컬럼 예: TMP(기온), REH(습도), VEC(풍향), WSD(풍속), POP(강수확률),
                 PTY(강수형태 0없음 1비 2비/눈 3눈 4소나기), PCP(강수량), SNO(신적설),
                 TMN/TMX(일 최저/최고기온, 해당 시각 행에만 값이 있음)
    """
    base = base or latest_base_time()
    params = {
        "serviceKey": api_key or load_api_key(),
        "pageNo": 1,
        "numOfRows": 1000,
        "dataType": "JSON",
        "base_date": base.strftime("%Y%m%d"),
        "base_time": base.strftime("%H%M"),
        **grid,
    }
    items = pd.DataFrame(_get(VILAGE_FCST_URL, params))
    items["시각"] = pd.to_datetime(items["fcstDate"] + items["fcstTime"], format="%Y%m%d%H%M")

    table = items.pivot(index="시각", columns="category", values="fcstValue")
    numeric = ["TMP", "REH", "VEC", "WSD", "POP", "PTY", "TMN", "TMX"]
    for col in numeric:
        if col in table:
            table[col] = pd.to_numeric(table[col], errors="coerce")
    table.attrs["발표시각"] = base
    return table
