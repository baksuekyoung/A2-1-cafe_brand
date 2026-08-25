"""[1] 브리프 규격 검증 — `docs/데이터-계약.md` 의 [1] 절을 기준으로 한다.

`brand_name_hint` · `extra` 를 쓰던 옛 규격으로 되돌아가면 여기서 걸린다.
"""

import json
from pathlib import Path

from brand_result import validate

SAMPLE_PATH = Path(__file__).resolve().parent.parent / "samples" / "brief.json"


def test_샘플_브리프가_규격을_통과한다():
    brief = json.loads(SAMPLE_PATH.read_text(encoding="utf-8"))
    assert validate.check_brief(brief) == []


def test_샘플_브리프가_규격의_여섯_필드를_그대로_쓴다():
    brief = json.loads(SAMPLE_PATH.read_text(encoding="utf-8"))
    assert set(brief) == {"industry", "target", "keywords", "tone", "competitors", "notes"}
    # 옛 규격의 흔적이 남아 있으면 안 된다
    assert "brand_name_hint" not in brief
    assert "extra" not in brief


def test_필수_세_개만_있어도_통과한다():
    """tone·competitors·notes 는 [1] 이 기본값을 채우므로 선택이다."""
    assert validate.check_brief({
        "industry": "카페", "target": "직장인", "keywords": ["여유", "감성"],
    }) == []


def test_필수_필드가_없으면_잡는다():
    problems = validate.check_brief({"keywords": ["여유", "감성"]})
    assert any("industry" in p for p in problems)
    assert any("target" in p for p in problems)


def test_필수_필드가_비어_있으면_잡는다():
    problems = validate.check_brief({
        "industry": "  ", "target": "직장인", "keywords": ["여유", "감성"],
    })
    assert any("industry" in p and "비어" in p for p in problems)


def test_키워드가_하나면_잡는다():
    problems = validate.check_brief({
        "industry": "카페", "target": "직장인", "keywords": ["여유"],
    })
    assert any("keywords" in p for p in problems)


def test_competitors_가_리스트가_아니면_잡는다():
    problems = validate.check_brief({
        "industry": "카페", "target": "직장인", "keywords": ["여유", "감성"],
        "competitors": "블루보틀",
    })
    assert any("competitors" in p for p in problems)


def test_dict_가_아니면_바로_잡는다():
    assert validate.check_brief("카페") == ["[1] brief 가 dict 가 아닙니다"]
