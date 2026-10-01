"""비/눈 판별 모델의 입력 Feature.

학습(과거 관측)과 서비스(기상청 예보)에서 똑같은 Feature를 만들 수 있도록
예보에서도 받을 수 있는 값만 사용한다.

| Feature | 관측(ASOS 일자료)       | 예보(단기예보)            |
|---------|------------------------|--------------------------|
| 최저기온 | 최저기온(°C)            | TMN                      |
| 최고기온 | 최고기온(°C)            | TMX                      |
| 평균기온 | 평균기온(°C)            | TMP(1시간 기온)의 하루 평균 |
| 평균습도 | 평균 상대습도(%)        | REH(습도)의 하루 평균      |
| 이슬점   | 평균기온·평균습도로 계산 | 평균기온·평균습도로 계산    |
| 북서풍   | 최다풍향(16방위)        | VEC(풍향)의 최빈값          |
"""
import numpy as np
import pandas as pd

FEATURES = ["최저기온", "최고기온", "평균기온", "평균습도", "이슬점", "북서풍"]


def dew_point(temp_c, rh_pct):
    """기온(°C)과 상대습도(%)로 이슬점(°C)을 계산한다 (Magnus 공식)."""
    a, b = 17.62, 243.12
    gamma = np.log(np.asarray(rh_pct, dtype=float) / 100) + a * temp_c / (b + temp_c)
    return b * gamma / (a - gamma)


def wet_bulb(temp_c, rh_pct):
    """기온(°C)과 상대습도(%)로 습구온도(°C)를 계산한다 (Stull 2011 근사식).

    습구온도는 젖은 천으로 감싼 온도계의 온도로, 공기가 건조할수록 기온보다 많이 낮다.
    눈송이가 떨어지며 녹을지를 기온보다 잘 설명해서 비/눈 구분에 널리 쓰인다.
    """
    t = np.asarray(temp_c, dtype=float)
    rh = np.asarray(rh_pct, dtype=float)
    return (t * np.arctan(0.151977 * np.sqrt(rh + 8.313659))
            + np.arctan(t + rh) - np.arctan(rh - 1.676331)
            + 0.00391838 * rh ** 1.5 * np.arctan(0.023101 * rh)
            - 4.686035)


def is_northwest(direction_deg):
    """풍향이 북서쪽(250~340도)이면 1. 대륙의 찬 공기가 들어오는 방향."""
    return pd.Series(direction_deg).between(250, 340).astype(int).to_numpy()


def daily_features(df):
    """ASOS 일자료 DataFrame → 모델 입력 Feature DataFrame."""
    out = pd.DataFrame(index=df.index)
    out["최저기온"] = df["최저기온(°C)"]
    out["최고기온"] = df["최고기온(°C)"]
    out["평균기온"] = df["평균기온(°C)"]
    out["평균습도"] = df["평균 상대습도(%)"]
    out["이슬점"] = dew_point(out["평균기온"], out["평균습도"])
    out["북서풍"] = is_northwest(df["최다풍향(16방위)"])
    return out[FEATURES]


# 시간별 모델 Feature (단기예보: TMP→기온, REH→습도, WSD→풍속, VEC→풍향)
HOURLY_FEATURES = ["기온", "습도", "습구온도", "이슬점", "풍속", "북서풍"]


def hourly_features(df):
    """시간별 기온·습도·풍속·풍향 → 모델 입력 Feature.

    관측(ASOS 시간자료)과 예보(단기예보)에 똑같이 쓰도록, 이슬점도 관측값 대신 기온·습도로 계산한다.
    """
    out = pd.DataFrame(index=df.index)
    out["기온"] = df["기온"]
    out["습도"] = df["습도"]
    out["습구온도"] = wet_bulb(df["기온"], df["습도"])
    out["이슬점"] = dew_point(df["기온"], df["습도"])
    out["풍속"] = df["풍속"]
    out["북서풍"] = is_northwest(df["풍향"])
    return out[HOURLY_FEATURES]
