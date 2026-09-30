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
