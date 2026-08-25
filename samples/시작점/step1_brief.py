"""[1] 브랜드 브리프 — 담당: 김준오 · 이태우

김준오님이 `#1단계` 채널(2026-08-25)에 올린 규격을 그대로 씁니다.
필수: `industry` `target` `keywords`  /  선택: `tone` `competitors` `notes`

김준오님 코드가 오면 이 파일은 **얇은 연결 껍데기**만 남습니다.
아래 두 줄 중 하나만 살리면 됩니다.
"""

import json
from pathlib import Path

BRIEF_PATH = Path(__file__).resolve().parent / "samples" / "brief.json"


def load_brief() -> dict:
    """docs/데이터-계약.md 의 [1] 규격대로 dict 를 돌려준다."""
    # 👉 김준오님 코드가 붙으면 이렇게 바꿉니다:
    #        from main import load_and_validate_brief
    #        return load_and_validate_brief(input("브리프 JSON 경로: "))
    #    그때까지는 아래 샘플로 파이프라인 전체를 돌려 볼 수 있습니다.
    return json.loads(BRIEF_PATH.read_text(encoding="utf-8"))


if __name__ == "__main__":
    # 한글 윈도우 콘솔(cp949)은 '—' 같은 글자에서 죽는다. 혼자 돌려 볼 때를 위한 안전장치.
    import sys
    for _stream in (sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8", errors="replace")

    # 자기 파트만 따로 돌려 볼 때 씁니다.
    print(json.dumps(load_brief(), ensure_ascii=False, indent=2))
