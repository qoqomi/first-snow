"""비/눈 판별 모델: 강수가 있는 날, 그 강수가 눈일 확률을 계산한다."""
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .config import MODEL_DIR
from .features import FEATURES, daily_features

# 눈이 올 수 있는 달 (10월 ~ 이듬해 4월)
SNOW_SEASON_MONTHS = [10, 11, 12, 1, 2, 3, 4]


def training_set(df):
    """눈 시즌의 강수일만 골라 (Feature, 눈 여부)를 만든다."""
    days = df[df["강수"] & df["일시"].dt.month.isin(SNOW_SEASON_MONTHS)]
    X = daily_features(days)
    ok = X.notna().all(axis=1)
    return days[ok], X[ok], days.loc[ok, "눈"].astype(int)


def build_model():
    return make_pipeline(StandardScaler(), LogisticRegression())


def save_model(model, name, meta=None):
    MODEL_DIR.mkdir(exist_ok=True)
    path = MODEL_DIR / f"{name}.joblib"
    joblib.dump({"model": model, "features": FEATURES, "meta": meta or {}}, path)
    return path


def load_model(name):
    return joblib.load(MODEL_DIR / f"{name}.joblib")
