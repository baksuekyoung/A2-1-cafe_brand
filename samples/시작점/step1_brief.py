"""[1] 브랜드 브리프 — 담당: 미정

`samples/brief.json` 을 읽어 그대로 돌려줍니다.
주제가 카페로 정해졌으니 값은 이미 채워져 있습니다.

고칠 것이 있다면 파이썬이 아니라 `samples/brief.json` 을 고치세요.
"""

import json
from pathlib import Path

BRIEF_PATH = Path(__file__).resolve().parent / "samples" / "brief.json"


def load_brief() -> dict:
    """docs/데이터-계약.md 의 [1] 규격대로 dict 를 돌려준다."""
    # 👉 여기를 채웁니다 — 파일 대신 화면에서 입력받고 싶다면 input() 으로 바꾸세요.
    #    다만 돌려주는 형식(키 이름)은 계약대로 두어야 합니다.
    return json.loads(BRIEF_PATH.read_text(encoding="utf-8"))


if __name__ == "__main__":
    # 자기 파트만 따로 돌려 볼 때 씁니다.
    print(json.dumps(load_brief(), ensure_ascii=False, indent=2))
