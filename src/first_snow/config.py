"""프로젝트 전역 설정."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
MODEL_DIR = ROOT / "models"

# 기상청 ASOS 서울 관측소
STATION_ID = 108

# 기상청 단기예보 격자 좌표 (서울 종로구 송월동 관측소 부근)
SEOUL_GRID = {"nx": 60, "ny": 127}

# 기사(일기 현상) 컬럼에서 눈 계열 현상 / 전체 강수 현상을 찾는 정규식
# 우박·싸락우박·얼음싸라기는 얼음 알갱이라 눈에서 제외한다.
SNOW_KINDS = ["눈", "진눈깨비", "소낙눈", "싸락눈", "가루눈", "소낙성진눈깨비"]
RAIN_KINDS = ["비", "이슬비", "소나기"]

SNOW_PATTERN = r"\{(?:" + "|".join(SNOW_KINDS) + r")\}"
PRECIP_PATTERN = r"\{(?:" + "|".join(RAIN_KINDS + SNOW_KINDS) + r")\}"

# ASOS 시간자료의 국내식 일기현상 코드 (dmstMtphNo, 2자리씩 이어붙여 기록됨)
# 2000~2025년 시간자료를 같은 날 일자료 기사와 맞춰 보고 확인한 값.
# 일자료 첫눈 기준(SNOW_KINDS)과 같게 눈 계열을 모두 포함하고, 우박류(12~14)는 제외한다.
HOURLY_RAIN_CODES = {"01": "비", "02": "이슬비", "04": "소나기"}
HOURLY_SNOW_CODES = {
    "05": "눈", "06": "진눈깨비", "08": "소낙눈",
    "09": "소낙성진눈깨비", "10": "싸락눈", "11": "가루눈",
}

# 첫눈 시즌: 9월 1일부터 센다
SEASON_START_MONTH = 9
