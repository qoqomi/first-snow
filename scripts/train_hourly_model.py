"""시간별 관측으로 비/눈 판별 모델(v1)을 학습해서 models/에 저장한다.

실행: python scripts/train_hourly_model.py
"""
from sklearn.metrics import accuracy_score, brier_score_loss, roc_auc_score

from first_snow.data import first_snow_dates, load_daily, load_hourly
from first_snow.features import HOURLY_FEATURES
from first_snow.model import build_model, hourly_training_set, save_model

MODEL_NAME = "snow_hourly_v1"
TEST_FROM = "2016-07-01"   # v0과 같은 평가 기간 (2016/17 시즌부터)


def first_snow_hits(model, hourly, test_from):
    """평가 기간의 각 첫눈 날에 대해, 그날 강수 시간 중 가장 높은 눈 확률."""
    first = first_snow_dates(load_daily())
    first = first[first["일시"] >= test_from]

    hours, X, _ = hourly_training_set(hourly)
    prob = model.predict_proba(X)[:, 1]
    day_max = (hours.assign(확률=prob).groupby(hours["일시"].dt.normalize())["확률"].max())

    first["눈 확률"] = first["일시"].map(day_max)
    return first[["일시", "눈 확률"]]


def main():
    hourly = load_hourly()
    hours, X, y = hourly_training_set(hourly)
    print(f"학습 데이터: {hours['연도'].min()}~{hours['연도'].max()}년, 강수 {len(y)}시간 (눈 {y.sum()}시간)")

    # 1) 과거로 학습 → 최근 10시즌으로 평가
    train = hours["일시"] < TEST_FROM
    model = build_model().fit(X[train], y[train])
    prob = model.predict_proba(X[~train])[:, 1]

    hits = first_snow_hits(model, hourly, TEST_FROM)
    n_hit = int((hits["눈 확률"] >= 0.5).sum())
    metrics = {
        "test_period": f"{TEST_FROM} ~ {hours['일시'].max().date()}",
        "test_hours": int((~train).sum()),
        "accuracy": round(accuracy_score(y[~train], prob >= 0.5), 3),
        "brier": round(brier_score_loss(y[~train], prob), 3),
        "auc": round(roc_auc_score(y[~train], prob), 3),
        "first_snow_hits": f"{n_hit}/{len(hits)}",
    }
    print("평가:", metrics)
    print(hits.to_string(index=False))

    # 2) 서비스용 모델은 전체 기간으로 다시 학습
    final = build_model().fit(X, y)
    meta = {
        "trained_on": f"{hours['일시'].min().date()} ~ {hours['일시'].max().date()}",
        "train_hours": int(len(y)),
        "metrics": metrics,
    }
    print("저장:", save_model(final, MODEL_NAME, meta, features=HOURLY_FEATURES))


if __name__ == "__main__":
    main()
