"""관측 데이터 불러오기와 라벨(눈/강수/첫눈) 만들기."""
import pandas as pd

from .config import (DATA_DIR, HOURLY_RAIN_CODES, HOURLY_SNOW_CODES, PRECIP_PATTERN,
                     SEASON_START_MONTH, SNOW_PATTERN)

# ASOS 시간자료 API 컬럼 → 분석에서 쓸 이름
HOURLY_COLUMNS = {
    "tm": "일시", "ta": "기온", "rn": "강수량", "hm": "습도", "td": "이슬점",
    "ws": "풍속", "wd": "풍향", "ps": "해면기압", "dsnw": "적설", "dmstMtphNo": "현상코드",
}


def load_daily(data_dir=DATA_DIR):
    """기상청 ASOS 일자료 CSV를 모두 읽어 날짜순으로 합친다."""
    files = sorted(data_dir.glob("OBS_ASOS_DD_*.csv"))
    if not files:
        raise FileNotFoundError(f"{data_dir}에 OBS_ASOS_DD_*.csv 파일이 없습니다.")

    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    df["일시"] = pd.to_datetime(df["일시"])
    df = df.drop_duplicates("일시").sort_values("일시").reset_index(drop=True)

    # 비·눈이 오지 않은 날은 빈칸으로 기록된다
    df["일강수량(mm)"] = df["일강수량(mm)"].fillna(0)
    df["기사"] = df["기사"].fillna("")
    return add_labels(df)


def add_labels(df):
    """기사 컬럼으로 눈/강수 여부와 연도를 붙인다."""
    df = df.copy()
    df["연도"] = df["일시"].dt.year
    df["눈"] = df["기사"].str.contains(SNOW_PATTERN, regex=True)
    df["강수"] = df["기사"].str.contains(PRECIP_PATTERN, regex=True)
    return df


def first_snow_dates(df):
    """연도별 첫눈(9월 1일 이후 첫 눈 계열 현상) 행과 9월 1일 기준 일수."""
    autumn = df[df["눈"] & (df["일시"].dt.month >= SEASON_START_MONTH)]
    first = autumn.drop_duplicates("연도").reset_index(drop=True)

    season_start = pd.to_datetime(first["연도"].astype(str) + f"-{SEASON_START_MONTH:02d}-01")
    first["첫눈_일수"] = (first["일시"] - season_start).dt.days
    return first


def split_codes(code):
    """'0605' → ['06', '05']. 시간자료 현상코드는 2자리 코드가 이어붙어 있다.

    일부 연도는 맨 앞의 0이 빠진 채 기록되어 있어서('0601' → '601', '01' → '1')
    짝수 길이가 되도록 앞에 0을 채운 뒤 자른다.
    """
    code = code.strip() if isinstance(code, str) else ""
    if len(code) % 2:
        code = "0" + code
    return [code[i:i + 2] for i in range(0, len(code), 2)]


def load_hourly(data_dir=DATA_DIR / "hourly"):
    """ASOS 시간자료 CSV(scripts/download_asos_hourly.py로 받은 것)를 읽어 라벨을 붙인다."""
    files = sorted(data_dir.glob("asos_hourly_*.csv"))
    if not files:
        raise FileNotFoundError(f"{data_dir}에 시간자료가 없습니다. scripts/download_asos_hourly.py를 먼저 실행하세요.")

    df = pd.concat([pd.read_csv(f, dtype={"dmstMtphNo": str}) for f in files], ignore_index=True)
    df = df[list(HOURLY_COLUMNS)].rename(columns=HOURLY_COLUMNS)
    df["일시"] = pd.to_datetime(df["일시"])
    df = df.drop_duplicates("일시").sort_values("일시").reset_index(drop=True)

    codes = df["현상코드"].map(split_codes)
    df["눈"] = codes.map(lambda cs: any(c in HOURLY_SNOW_CODES for c in cs)).astype("boolean")
    df["강수"] = df["눈"] | codes.map(lambda cs: any(c in HOURLY_RAIN_CODES for c in cs))
    df["강수량"] = df["강수량"].fillna(0)
    df["연도"] = df["일시"].dt.year

    # 1996~1999년 시간자료에는 현상코드가 아예 기록되지 않았다.
    # 코드가 없는 연도는 "비·눈 없음"이 아니라 "모름"으로 둔다.
    has_codes = df.groupby("연도")["현상코드"].transform(lambda s: s.notna().any())
    df.loc[~has_codes, ["눈", "강수"]] = pd.NA
    return df
