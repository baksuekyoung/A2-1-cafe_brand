"""[1] 브랜드 브리프

브랜드 브리프 JSON 을 읽어 검증한 뒤 dict 로 넘긴다.

필수: `industry` `target` `keywords`  /  선택: `tone` `competitors` `notes`
"""

import json
from pathlib import Path

BRIEF_PATH = Path(__file__).resolve().parent / "samples" / "brief.json"


def load_brief() -> dict:
    """docs/데이터-계약.md 의 [1] 규격대로 dict 를 돌려준다."""
    # 👉 [1] 구현이 붙으면 이렇게 바꾼다:
    #        from main import load_and_validate_brief
    #        return load_and_validate_brief(input("브리프 JSON 경로: "))
    #    그때까지는 아래 샘플로 파이프라인 전체를 실행할 수 있다.
    return json.loads(BRIEF_PATH.read_text(encoding="utf-8"))


if __name__ == "__main__":
    # 한글 윈도우 콘솔(cp949)은 '—' 같은 글자에서 죽는다. 혼자 돌려 볼 때를 위한 안전장치.
    import sys
    for _stream in (sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8", errors="replace")

    # 자기 파트만 따로 돌려 볼 때 씁니다.
    print(json.dumps(load_brief(), ensure_ascii=False, indent=2))
