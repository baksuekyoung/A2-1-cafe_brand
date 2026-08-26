"""[1] 브랜드 브리프

브랜드 브리프 JSON 을 읽어 검증한 뒤 dict 로 넘긴다.

필수: `industry` `target` `keywords`  /  선택: `tone` `competitors` `notes`

## 이 파일과 main.py 의 관계

읽고 검증하는 알맹이는 **`main.load_brief(경로)`** 하나뿐이다. 여기서 그것을 부른다.
같은 이름의 함수를 두 벌 두면 한쪽만 고쳐져 서로 다르게 동작한다.

    main.py    경로를 물어보고(대화형) → main.load_brief(경로) 로 검증
    brief.py   경로를 안 받고 → 같은 main.load_brief() 로 기본 브리프를 검증

`integrate.py` 를 단독으로 돌릴 때(=사람에게 물어볼 수 없을 때) 쓰라고 둔 자리다.
`main.py` 로 들어오면 이미 검증된 브리프가 넘어오므로 이 함수는 불리지 않는다.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

# 기본으로 읽을 브리프. `BRIEF_PATH` 환경변수로 바꿀 수 있다 —
# integrate.py 를 단독으로 돌리면서 다른 브리프를 쓰고 싶을 때를 위한 것이다.
DEFAULT_BRIEF = Path(__file__).resolve().parent / "samples" / "brief.json"


def brief_path() -> Path:
    """읽을 브리프 경로. 환경변수가 있으면 그것을 쓴다."""
    지정 = (os.environ.get("BRIEF_PATH") or "").strip()
    return Path(지정) if 지정 else DEFAULT_BRIEF


def load_brief() -> dict:
    """docs/데이터-계약.md 의 [1] 규격대로 dict 를 돌려준다.

    검증은 `main.load_brief` 가 한다 — 필수 필드·자료형·JSON 문법을 모두 본다.
    예전에는 여기서 `json.loads` 만 하고 검증을 건너뛰어, 필수 필드가 없는
    브리프도 그대로 통과했다.

    Raises:
        main.BriefError: 파일이 없거나 규격에 어긋난 경우.
            `runner.run_step` 이 잡아 리포트에 남긴다.
    """
    from main import load_brief as 읽고_검증한다

    return 읽고_검증한다(str(brief_path()))


if __name__ == "__main__":
    # 한글 윈도우 콘솔(cp949)은 '—' 같은 글자에서 죽는다. 혼자 돌려 볼 때를 위한 안전장치.
    import sys
    for _stream in (sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8", errors="replace")

    # 자기 파트만 따로 돌려 볼 때 씁니다.
    print(json.dumps(load_brief(), ensure_ascii=False, indent=2))
