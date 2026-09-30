"""관측 데이터 불러오기와 라벨(눈/강수/첫눈) 만들기."""
import pandas as pd

from .config import DATA_DIR, PRECIP_PATTERN, SEASON_START_MONTH, SNOW_PATTERN


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
