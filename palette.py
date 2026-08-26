"""[3] 컬러 팔레트

LLM 에게 브랜드에 맞는 색을 고르게 한다.

브리프만 넣으면 "카페니까 갈색" 같은 결과가 나온다. [2] 가 확정한 브랜드명과
스토리를 함께 넣어야 글과 색이 따로 놀지 않는다.

키가 없거나 호출이 실패하면 EXAMPLE 을 돌려준다 — 파이프라인을 멈추지 않는다.
어느 쪽을 썼는지는 `used_example` 로 알린다.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

# [2] 가 만들어 둔 호출 경로를 그대로 쓴다. 같은 HTTP 코드를 두 벌 두지 않는다.
from naming import _pick_provider

try:
    from dotenv import load_dotenv
except ImportError:  # python-dotenv 가 없어도 환경변수로 넣었을 수 있다
    def load_dotenv(*_args, **_kwargs) -> bool:
        return False

ENV_PATH = Path(__file__).resolve().parent / ".env"

HEX_PATTERN = re.compile(r"^#[0-9A-F]{6}$")

MIN_SUBS = 2
MAX_SUBS = 3

# 로고는 흰 배경 위에 메인 컬러로 그린다. 메인이 흰색에 가까우면 그림이 흐려진다.
# 실측 #C5B29A(대비 2.06:1)로 그린 로고가 거의 안 보였다.
MIN_MAIN_CONTRAST = 3.0

# 계약이 요구하는 것 — 메인 1개, 서브 2개 이상. hex 는 '#RRGGBB' 대문자
EXAMPLE = {
    "main": {"hex": "#3E3028", "name": "로스팅 브라운", "reason": "원두를 볶은 색에서 가져왔습니다"},
    "subs": [
        {"hex": "#F5F0E8", "name": "크림", "reason": "여백을 만들고 글자를 읽기 쉽게 합니다"},
        {"hex": "#7C9070", "name": "세이지", "reason": "차분함을 더하는 포인트 색입니다"},
    ],
}

PALETTE_RULE = (
    f"메인 컬러 1개와 서브 컬러 {MIN_SUBS}~{MAX_SUBS}개를 고르세요.\n"
    "  - 메인은 간판·로고에 쓸 대표색입니다. 브랜드의 성격이 한눈에 드러나야 합니다.\n"
    "    **흰 배경 위에 또렷하게 보일 만큼 진해야 합니다.** 로고를 이 색으로 그립니다.\n"
    "    베이지·아이보리처럼 흰색에 가까운 색을 메인으로 고르면 로고가 흐려집니다.\n"
    "  - 서브 중 하나는 배경으로 쓸 밝은 색으로 잡으세요. 여백이 있어야 글이 읽힙니다.\n"
    "  - 나머지 서브는 포인트 색입니다. 메인과 같은 계열로 가면 밋밋해집니다.\n"
    "hex 는 반드시 '#' 을 붙인 6자리 **대문자**로 씁니다.\n"
    "  '#3E3028' 이 맞습니다. '3e3028' 이나 'rgb(62,48,40)' 은 안 됩니다.\n"
    "name 은 사람이 부를 색 이름을 한글로 짧게 씁니다 (예: 로스팅 브라운).\n"
    "reason 은 이 브랜드에 왜 이 색인지 한 문장으로 씁니다.\n"
    "업종만 보고 흔한 색을 고르지 마세요. 브랜드명과 스토리에 실제로 닿아야 합니다."
)

RESPONSE_SHAPE = (
    '{"main": {"hex": "#RRGGBB", "name": "색 이름", "reason": "고른 이유"}, '
    '"subs": [{"hex": "#RRGGBB", "name": "색 이름", "reason": "고른 이유"}]}'
)


def build_prompt(brief: dict, naming: dict | None) -> str:
    """브리프와 [2] 결과를 프롬프트에 녹인다.

    Args:
        brief: [1] 이 검증해 넘긴 브리프.
        naming: [2] 결과. 앞 단계가 실패했으면 None 일 수 있다.
    """
    keywords = ", ".join(str(k) for k in brief.get("keywords") or [])

    lines = [
        "당신은 브랜드 컬러 디렉터입니다. 아래 브랜드에 맞는 컬러 팔레트를 고르세요.",
        "",
        f"업종: {brief.get('industry', '')}",
        f"타깃: {brief.get('target', '')}",
        f"키워드: {keywords}",
    ]
    if brief.get("tone"):
        lines.append(f"톤앤매너: {brief['tone']}")

    # [2] 가 확정한 이름과 스토리를 넣는다. 없으면 브리프만으로 만든다.
    for label, value in _naming_hints(naming):
        lines.append(f"{label}: {value}")

    lines += ["", PALETTE_RULE, "",
              f"아래 JSON 형식으로만 답하세요. 다른 말은 붙이지 마세요.\n{RESPONSE_SHAPE}"]
    return "\n".join(lines)


def _naming_hints(naming: dict | None) -> list[tuple[str, str]]:
    """[2] 결과에서 프롬프트에 넣을 것만 추린다. 형태가 어긋나면 조용히 건너뛴다."""
    if not isinstance(naming, dict):
        return []

    hints = []
    candidates = naming.get("naming")
    if isinstance(candidates, list) and candidates:
        first = candidates[0]
        if isinstance(first, dict) and first.get("name"):
            hints.append(("확정 브랜드명", str(first["name"])))
            if first.get("meaning"):
                hints.append(("이름의 뜻", str(first["meaning"])))

    slogans = naming.get("slogans")
    if isinstance(slogans, list) and slogans:
        hints.append(("슬로건", str(slogans[0])))

    story = naming.get("story")
    if isinstance(story, str) and story.strip():
        hints.append(("브랜드 스토리", story.strip()))
    return hints


def _normalize(data: dict) -> dict:
    """모델이 준 것을 계약 형식으로 다듬는다.

    hex 소문자·'#' 누락처럼 자주 나는 형식 오류는 여기서 고친다.
    고칠 수 없는 값은 그대로 두고 [5] 의 검증이 잡게 한다.

    Raises:
        ValueError: main 이나 subs 가 아예 없는 경우.
    """
    if not isinstance(data, dict):
        raise ValueError("팔레트가 객체가 아닙니다")

    main = _normalize_color(data.get("main"))
    if main is None:
        raise ValueError("main 이 없습니다")

    subs = [c for c in (_normalize_color(s) for s in data.get("subs") or []) if c]
    if len(subs) < MIN_SUBS:
        raise ValueError(f"subs 가 {len(subs)}개입니다 ({MIN_SUBS}개 이상 필요)")

    return {"main": main, "subs": subs[:MAX_SUBS]}


def _normalize_color(color: object) -> dict | None:
    """색 하나를 다듬는다. 쓸 수 없으면 None."""
    if not isinstance(color, dict):
        return None

    hex_value = str(color.get("hex") or "").strip().upper()
    if hex_value and not hex_value.startswith("#"):
        hex_value = "#" + hex_value          # '3E3028' 로 오는 일이 잦다
    if not HEX_PATTERN.match(hex_value):
        return None                          # 세 자리 축약·rgb() 등은 버린다

    return {
        "hex": hex_value,
        "name": str(color.get("name") or "").strip() or hex_value,
        "reason": str(color.get("reason") or "").strip(),
    }


def generate_palette(brief: dict, naming: dict | None = None) -> dict:
    """docs/데이터-계약.md 의 [3] 규격대로 dict 를 돌려준다.

    Args:
        brief: [1] 이 검증해 넘긴 브리프.
        naming: [2] 결과. 없으면 브리프만으로 만든다.

    Returns:
        `{"main": {...}, "subs": [...]}`. 예시 값을 썼으면 `used_example` 이 True.
    """
    load_dotenv(ENV_PATH)
    provider, api_key, call = _pick_provider()

    if not api_key:
        print("   ℹ️  [3] API 키가 없어 예시 값으로 돌립니다"
              " (.env 에 OPENAI_API_KEY 또는 GEMINI_API_KEY)")
        return dict(EXAMPLE, used_example=True)

    try:
        palette = _normalize(call(build_prompt(brief, naming), api_key))
    except Exception as exc:
        print(f"   ⚠️  [3] {provider} 호출 실패({exc}) — 예시 값으로 대신합니다")
        return dict(EXAMPLE, used_example=True)

    palette = _retry_if_main_too_light(palette, brief, naming, api_key, call)

    print(f"   🤖 [3] {provider} 로 생성했습니다"
          f" (메인 {palette['main']['hex']} · 서브 {len(palette['subs'])}개)")
    return palette


def _main_contrast(palette: dict) -> float:
    """메인 컬러와 흰 배경의 명도 대비. 계산할 수 없으면 충분한 것으로 본다."""
    try:
        from brand_result.store import contrast_ratio

        return contrast_ratio(palette["main"]["hex"], "#FFFFFF")
    except Exception:
        return MIN_MAIN_CONTRAST


def _retry_if_main_too_light(palette: dict, brief: dict, naming: dict | None,
                             api_key: str, call) -> dict:
    """메인이 흰 배경에 묻히면 한 번만 다시 청한다.

    로고를 이 색으로 그리므로, 메인이 흰색에 가까우면 시안 전체가 흐려진다.
    다시 받은 것도 밝으면 원래 것을 쓴다 — 색은 사람이 판단할 문제이고,
    대비 경고는 `brand_result.md` 에 남는다.
    """
    before = _main_contrast(palette)
    if before >= MIN_MAIN_CONTRAST:
        return palette

    ask = (
        f"고른 메인 컬러 {palette['main']['hex']} 는 흰 배경 대비가 {before:.2f}:1 로"
        " 너무 밝습니다. 이 색으로 로고를 그리면 형태가 보이지 않습니다.\n"
        f"흰 배경 대비 {MIN_MAIN_CONTRAST:.0f}:1 이상이 되도록"
        " **더 진한 색으로 메인만 바꿔** 다시 고르세요.\n"
        "밝은 색이 필요하면 그것은 서브로 내리세요. 서브는 그대로 두어도 됩니다.\n\n"
        + build_prompt(brief, naming)
    )
    try:
        after = _normalize(call(ask, api_key))
    except Exception:
        return palette

    if _main_contrast(after) > before:
        print(f"   🔁 [3] 메인이 흰 배경에 묻혀 다시 청했습니다"
              f" ({palette['main']['hex']} -> {after['main']['hex']})")
        return after
    return palette


if __name__ == "__main__":
    # 한글 윈도우 콘솔(cp949)은 '—' 같은 글자에서 죽는다. 혼자 돌려 볼 때를 위한 안전장치.
    import sys
    for _stream in (sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8", errors="replace")

    # 자기 파트만 따로 돌려 볼 때 씁니다.
    #   python palette.py
    brief_path = Path(__file__).resolve().parent / "samples" / "brief.json"
    sample = json.loads(brief_path.read_text(encoding="utf-8")) if brief_path.exists() else {}
    print(json.dumps(generate_palette(sample), ensure_ascii=False, indent=2))
