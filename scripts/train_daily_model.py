"""일별 관측으로 비/눈 판별 모델(v0)을 학습해서 models/에 저장한다.

실행: python scripts/train_daily_model.py
"""
from sklearn.metrics import accuracy_score, brier_score_loss, roc_auc_score

from first_snow.data import load_daily
from first_snow.model import build_model, save_model, training_set

MODEL_NAME = "snow_daily_v0"
TEST_FROM = "2016-07-01"   # 2016/17 시즌부터 평가용


def main():
    df = load_daily()
    days, X, y = training_set(df)

    # 1) 과거로 학습 → 최근 10시즌으로 평가
    train = days["일시"] < TEST_FROM
    model = build_model().fit(X[train], y[train])
    prob = model.predict_proba(X[~train])[:, 1]
    metrics = {
        "test_period": f"{TEST_FROM} ~ {days['일시'].max().date()}",
        "test_days": int((~train).sum()),
        "accuracy": round(accuracy_score(y[~train], prob >= 0.5), 3),
        "brier": round(brier_score_loss(y[~train], prob), 3),
        "auc": round(roc_auc_score(y[~train], prob), 3),
    }
    print("평가:", metrics)

    # 2) 서비스용 모델은 전체 기간으로 다시 학습
    final = build_model().fit(X, y)
    meta = {
        "trained_on": f"{days['일시'].min().date()} ~ {days['일시'].max().date()}",
        "train_days": int(len(y)),
        "metrics": metrics,
    }
    path = save_model(final, MODEL_NAME, meta)
    print("저장:", path)


if __name__ == "__main__":
    main()
