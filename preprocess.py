import pandas as pd

file1 = pd.read_csv("./data/OBS_ASOS_DD_20260923125529.csv", encoding="cp949")
file2 = pd.read_csv("./data/OBS_ASOS_DD_20260923125852.csv", encoding="cp949")
file3 = pd.read_csv("./data/OBS_ASOS_DD_20260923130020.csv", encoding="cp949")

df = pd.concat([file1, file2, file3], ignore_index=True)

print(df.shape)

# 날짜 타입으로 변환
df["일시"] = pd.to_datetime(df["일시"])

# 눈이 관측된 날
snow_days = df[
    df["기사"].fillna("").str.contains(r"\{눈\}", regex=True)
].copy()

# 9월 이후만
snow_days = snow_days[snow_days["일시"].dt.month >= 9]

# 연도 생성
snow_days["연도"] = snow_days["일시"].dt.year

# 연도별 가장 처음 눈이 관측된 날짜
first_snow = (
    snow_days
    .sort_values("일시")
    .groupby("연도")
    .first()
    .reset_index()
)

print(first_snow[["연도", "일시"]])