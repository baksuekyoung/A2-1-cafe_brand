"""로고 시안용 영어 프롬프트를 만든다.

## 왜 따로 떼어 놓았나

한국어 브리프를 이미지 API 에 그대로 넘기면 엉뚱한 그림이 나온다.
`"20-30대 직장인"` 을 인물 사진 요청으로 읽어 로고 자리에 사람 얼굴이 나온 적이 있다.
그래서 **이미지 API 에 넘기기 전에 영어로 옮긴다.**

옮기는 방법은 두 가지다.

1. `OPENAI_API_KEY` 가 있으면 LLM 에게 영어 장면 묘사를 시킨다 (제일 정확하다)
2. 없으면 아래 낱말표로 옮기고, 표에 없는 낱말은 **넣지 않는다**

2번에서 "표에 없으면 그냥 한국어로 넣는다" 로 두면 안 된다.
그 순간 위에 적은 사고가 그대로 재현된다. 모르는 낱말은 빼는 편이 낫다.

## HEX 대신 색 이름을 쓰는 이유

이미지 모델은 `#3E3028` 을 거의 무시하고 `roasted coffee brown` 은 알아듣는다.
"""

from __future__ import annotations

import json
import os
import urllib.request

# 로고답게 나오게 하는 최소 조건. 길게 쓰면 무료 모델이 흘려버린다.
STYLE = "flat vector logo mark, minimal, plain white background, no text, centered"

LOGO_COUNT = 2  # 명세는 2~3장을 요구한다

CONCEPTS = (
    "a simple abstract mark symbolizing {theme}",
    "a single clean icon representing {theme}, geometric line art",
)

# ChatGPT·Copilot 같은 **대화형** 도구에 넣을 때 쓰는 문장.
#
# 위의 쉼표 나열식(tag) 프롬프트는 Stable Diffusion 계열 API 용이다.
# 대화형 도구에 그대로 넣으면 두 가지 이유로 그림이 안 나온다.
#
#   1. "logo for a brand called OO" 는 상표 정책에 걸려 거절당하는 일이 잦다.
#      → 브랜드 이름을 빼고 '아이콘·심볼' 을 설명한다.
#   2. 쉼표로 나열한 낱말 뭉치를 지시문으로 읽고 되묻기만 한다.
#      → 온전한 문장으로 쓴다.
HUMAN_CONCEPTS = (
    "a minimalist abstract symbol that suggests {theme}",
    "a single clean geometric icon that suggests {theme}, drawn in thin even lines",
)

HUMAN_TEMPLATE = (
    "Draw {concept}. "
    "Flat vector illustration style, centered in the frame with generous empty space "
    "around it. Use {color} as the only color, on a plain white background. "
    "Simple enough to recognize at a small size. "
    "Do not include any letters, words, or numbers anywhere in the image."
)

# 카페 브랜드 브리프에 자주 나오는 낱말. 없는 낱말은 프롬프트에서 뺀다.
KOREAN_TO_ENGLISH = {
    # 업종
    "카페": "cafe",
    "커피": "coffee",
    "베이커리": "bakery",
    "디저트": "dessert shop",
    "로스터리": "coffee roastery",
    # 키워드·정서
    "여유": "calm and unhurried ease",
    "따뜻함": "warmth",
    "온기": "warmth",
    "일상": "everyday life",
    "일상의 쉼표": "a pause in everyday life",
    "쉼표": "a comma-shaped pause",
    "쉼": "rest",
    "감성": "gentle sentiment",
    "휴식": "rest",
    "단정함": "tidy simplicity",
    "편안함": "comfort",
    "정성": "care and craft",
    "자연": "nature",
    "순수": "purity",
    "건강": "wellness",
    "손길": "a human touch",
    "향": "aroma",
    # 색 이름
    "로스팅 브라운": "roasted coffee brown",
    "브라운": "brown",
    "크림": "cream",
    "세이지": "sage green",
    "베이지": "beige",
    "아이보리": "ivory",
    "차콜": "charcoal",
    "네이비": "navy",
    "딥 네이비": "deep navy",
    "그린": "green",
    "테라코타": "terracotta",
}

DEFAULT_THEME = "quiet everyday comfort"
DEFAULT_COLOR = "warm neutral tones"
DEFAULT_INDUSTRY = "small local brand"


def _is_ascii(text: str) -> bool:
    return bool(text) and all(ord(char) < 128 for char in text)


def to_english(term: object) -> str:
    """한국어 낱말을 영어로 옮긴다. 옮길 수 없으면 빈 문자열."""
    text = str(term or "").strip()
    if not text:
        return ""
    if _is_ascii(text):
        return text  # 이미 영어면 그대로 쓴다
    return KOREAN_TO_ENGLISH.get(text, "")


def _brand_name(naming: object) -> str:
    """대표 이름의 영어 표기를 꺼낸다. 한글뿐이면 이름을 빼고 만든다.

    `온기(溫氣)` 처럼 괄호가 붙은 경우 괄호 안까지 넘기면 모델이 한자를
    그리려 든다. 영어 표기가 없으면 아예 넣지 않는 편이 낫다.
    """
    if not isinstance(naming, dict):
        return ""
    names = naming.get("naming")
    if not isinstance(names, list) or not names or not isinstance(names[0], dict):
        return ""

    first = names[0]
    for key in ("english", "en", "romanized"):
        candidate = str(first.get(key) or "").strip()
        if _is_ascii(candidate):
            return candidate

    name = str(first.get("name") or "").strip()
    return name if _is_ascii(name) else ""


def _color(palette: object) -> str:
    if isinstance(palette, dict):
        main = palette.get("main")
        if isinstance(main, dict):
            english = to_english(main.get("name"))
            if english:
                return f"{english} color palette"
    return DEFAULT_COLOR


def _themes(brief: dict) -> list[str]:
    """브리프 키워드 중 영어로 옮길 수 있는 것만 고른다."""
    themes = [to_english(word) for word in (brief.get("keywords") or [])]
    themes = [theme for theme in themes if theme]
    return themes or [DEFAULT_THEME]


def build_prompts(brief: dict, naming: object = None, palette: object = None,
                  count: int = LOGO_COUNT) -> list[str]:
    """이미지 생성 API 에 그대로 넣을 영어 프롬프트를 만든다.

    돌려주는 문자열에는 한국어가 들어가지 않는다.
    """
    brief = brief if isinstance(brief, dict) else {}
    industry = to_english(brief.get("industry")) or DEFAULT_INDUSTRY
    brand = _brand_name(naming)
    color = _color(palette)
    themes = _themes(brief)

    prompts = []
    for index in range(min(count, len(CONCEPTS))):
        theme = themes[index % len(themes)]
        subject = CONCEPTS[index].format(theme=theme)
        owner = f"a {industry} brand" + (f" called {brand}" if brand else "")
        prompts.append(f"{STYLE}, {subject}, for {owner}, {color}")
    return prompts


def build_human_prompts(brief: dict, palette: object = None,
                        count: int = LOGO_COUNT) -> list[str]:
    """ChatGPT 같은 **대화형** 도구에 넣을 프롬프트를 만든다.

    `build_prompts()` 와 다른 점 두 가지.

    - **브랜드 이름을 넣지 않는다.** "logo for a brand called OO" 는 상표 정책에
      걸려 거절당하는 일이 잦다. 이름은 나중에 사람이 얹으면 된다.
    - **온전한 문장으로 쓴다.** 쉼표로 나열한 낱말 뭉치를 넣으면 그림을 그리지
      않고 무엇을 원하는지 되묻기만 한다.
    """
    brief = brief if isinstance(brief, dict) else {}
    color = _color(palette).replace(" color palette", "")
    themes = _themes(brief)

    prompts = []
    for index in range(min(count, len(HUMAN_CONCEPTS))):
        theme = themes[index % len(themes)]
        concept = HUMAN_CONCEPTS[index].format(theme=theme)
        prompts.append(HUMAN_TEMPLATE.format(concept=concept, color=color))
    return prompts


def translate_with_llm(brief: dict, naming: object, palette: object,
                       count: int = LOGO_COUNT) -> list[str] | None:
    """LLM 에게 영어 프롬프트를 짓게 한다. 키가 없거나 실패하면 None.

    낱말표로는 못 옮기는 브리프(예: 다른 업종)도 이 경로면 제대로 나온다.
    """
    api_key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if not api_key:
        return None

    brand = ""
    if isinstance(naming, dict) and isinstance(naming.get("naming"), list):
        names = naming["naming"]
        if names and isinstance(names[0], dict):
            brand = str(names[0].get("name") or "")

    ask = (
        "아래 한국어 브랜드 정보를 읽고, 로고 이미지 생성 API 에 넣을 "
        f"**영어** 프롬프트 {count}개를 만드세요.\n\n"
        f"업종: {brief.get('industry', '')}\n"
        f"키워드: {', '.join(str(k) for k in (brief.get('keywords') or []))}\n"
        f"톤: {brief.get('tone', '')}\n"
        f"브랜드명: {brand}\n\n"
        "규칙:\n"
        f"- 각 프롬프트는 '{STYLE}' 로 시작합니다.\n"
        "- 100자 안팎으로 짧게 씁니다. 길면 모델이 흘려버립니다.\n"
        "- 한국어를 한 글자도 넣지 마세요. 색은 HEX 가 아니라 영어 색 이름으로 씁니다.\n"
        "- 사람·얼굴·사진을 요청하지 마세요. 로고 마크만 만듭니다.\n"
        '- {"prompts": ["...", "..."]} 형식의 JSON 으로만 답하세요.'
    )
    body = json.dumps({
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": ask}],
        "response_format": {"type": "json_object"},
    }).encode("utf-8")
    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {api_key}"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
        data = json.loads(payload["choices"][0]["message"]["content"])
    except Exception:
        return None

    prompts = [str(p).strip() for p in (data.get("prompts") or []) if str(p).strip()]
    # 한국어가 섞여 오면 쓰지 않는다. 낱말표 쪽이 차라리 안전하다.
    prompts = [p for p in prompts if _is_ascii(p)]
    return prompts[:count] or None


def make_prompts(brief: dict, naming: object = None, palette: object = None,
                 count: int = LOGO_COUNT) -> list[str]:
    """LLM 을 먼저 쓰고, 안 되면 낱말표로 만든다."""
    return translate_with_llm(brief, naming, palette, count) or \
        build_prompts(brief, naming, palette, count)


SOURCE_LABEL = {
    "openai": "OpenAI 이미지 API",
    "gemini": "Gemini 이미지 API",
    "pollinations": "Pollinations (무료)",
    "placeholder": "생성 실패 — 자리표시자",
}


def build_markdown(prompts: list[str], sources: list[str] | None = None,
                   human_prompts: list[str] | None = None) -> str:
    """`logo_prompts.md` 본문을 만든다.

    이미지 생성이 실패하거나 결과가 마음에 안 들어도 이 파일만 있으면
    사람이 직접 만들 수 있다.
    """
    lines = [
        "# 로고 시안 프롬프트",
        "",
        "> 한국어를 이미지 도구에 그대로 넘기면 로고가 아니라 인물 사진이 나오는 일이",
        "> 있어, 브리프를 영어 장면 묘사로 옮겨 적었습니다.",
        "",
    ]

    if human_prompts:
        lines += [
            "## 직접 만드실 때 (ChatGPT · Copilot 등)",
            "",
            "아래 문장을 **그대로 복사해서** 채팅창에 붙여 넣으십시오.",
            "",
            "> 브랜드 이름은 일부러 넣지 않았습니다.",
            "> `logo for a brand called ...` 처럼 쓰면 상표 정책에 걸려 거절당합니다.",
            "> 심볼을 먼저 받고, 이름은 그 위에 얹으시면 됩니다.",
            "",
        ]
        for index, prompt in enumerate(human_prompts, start=1):
            lines += [f"### 시안 {index}", "", "```text", prompt, "```", ""]
        lines += [
            "마음에 드는 그림이 나오면 `logo_01.png` · `logo_02.png` 로 저장해",
            "이 폴더에 넣으십시오. 결과 문서에 그대로 실립니다.",
            "",
            "---",
            "",
        ]

    lines += [
        "## 프로그램이 이미지 API 에 넣은 프롬프트",
        "",
        "쉼표로 나열한 형식입니다. **API 전용**이라 대화형 도구에 넣으면",
        "그림을 그리지 않고 무엇을 원하는지 되묻습니다.",
        "",
    ]
    for index, prompt in enumerate(prompts, start=1):
        lines += [f"### 시안 {index}", ""]
        if sources and index <= len(sources):
            label = SOURCE_LABEL.get(sources[index - 1], sources[index - 1])
            lines += [f"생성: {label}", ""]
        lines += ["```text", prompt, "```", ""]
    return "\n".join(lines)
