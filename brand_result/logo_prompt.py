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

# 이미지 API 에 넣는 프롬프트. 실제로 돌려 보고 고른 문장이다.
#
# 세 가지를 지켜야 글자 없는 로고가 나온다.
#
#   1. **"logo" 라는 낱말을 쓰지 않는다.** 모델이 상표를 흉내 내며 밑에 뭉개진
#      가짜 글씨를 같이 그린다. "icon" · "symbol" · "pictogram" 으로 부른다.
#   2. **배경을 문장 앞쪽에 못 박는다.** "pure white background" 를 빼면
#      배경이 브랜드 색으로 칠해져 나온다.
#   3. **글자 금지를 여러 표현으로 반복한다.** 한 번만 적으면 흘려버린다.
#
# 참고: Pollinations 의 `model=flux` 는 차이가 없었다 (같은 프롬프트로
# 바이트까지 같은 이미지가 나왔다). 결과를 바꾸는 것은 프롬프트 쪽이다.
STYLE = "minimalist geometric icon"  # 문서·테스트에서 가리키는 대표 낱말

# 명세는 2~3장을 요구한다. 기본은 2장이고, 환경변수 LOGO_COUNT 나
# `python main.py --logos 3` 으로 3장까지 올릴 수 있다.
LOGO_COUNT = 2
MAX_LOGO_COUNT = 3

PROMPT_TEMPLATES = (
    "minimalist geometric icon, single abstract symbol suggesting {theme}, "
    "solid {color} shape on pure white background, flat vector, "
    "no lettering, no words, no signature, no watermark, centered, lots of white space",

    "simple pictogram, one abstract mark suggesting {theme}, thick even strokes, "
    "solid {color} on pure white background, flat design, "
    "wordless, textless, no typography, no letters, no numbers, centered, negative space",

    "clean line-art emblem, a single continuous outline suggesting {theme}, "
    "even stroke weight, {color} lines on pure white background, flat vector, "
    "no fill, no shading, no text, no lettering, no characters, no caption, "
    "centered with wide margins",
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
    "an emblem made of one continuous outline that suggests {theme}, "
    "drawn with even stroke weight and no fill",
)

HUMAN_TEMPLATE = (
    "Draw {concept}. "
    "Flat vector illustration style, centered in the frame with generous empty space "
    "around it. Use {color} as the only color, on a pure white background. "
    "Simple enough to recognize at a small size. "
    "Do not include any letters, words, numbers, signature, or watermark anywhere "
    "in the image. The mark must be completely wordless."
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

    **브랜드 이름을 넣지 않는다.** `for a cafe brand called Yeobaek` 처럼 적으면
    모델이 그 이름을 그림 안에 써 넣으려 하고, 글자를 제대로 못 그려서
    뭉개진 가짜 글씨가 로고 아래 남는다. 이름은 사람이 나중에 얹으면 된다.
    `naming` 인자는 호출부 서명을 유지하려고 받되 쓰지 않는다.
    """
    brief = brief if isinstance(brief, dict) else {}
    color = _color(palette).replace(" color palette", "")
    themes = _themes(brief)

    prompts = []
    for index in range(min(count, len(PROMPT_TEMPLATES))):
        theme = themes[index % len(themes)]
        prompts.append(PROMPT_TEMPLATES[index].format(theme=theme, color=color))
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


def translate_themes_with_llm(brief: dict) -> list[str] | None:
    """LLM 에게 **키워드만** 영어로 옮기게 한다. 키가 없거나 실패하면 None.

    프롬프트 전체를 LLM 에게 맡기지 않는다. 예전에 그렇게 했더니 모델이
    검증된 규칙(흰 배경 · 글자 금지 · 정확한 색 이름)을 통째로 지워 버리고
    자기 문장으로 다시 썼다. 그래서 로고 색이 팔레트와 달라졌다.

    문장 구조는 `PROMPT_TEMPLATES` 가 쥐고, LLM 은 낱말표에 없는 한국어를
    옮기는 일만 맡는다.
    """
    api_key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    gemini_key = (os.environ.get("GEMINI_API_KEY") or "").strip()
    keywords = [str(k).strip() for k in (brief.get("keywords") or []) if str(k).strip()]
    if not keywords or not (api_key or gemini_key):
        return None

    ask = (
        "아래 한국어 낱말을 영어로 옮기세요. 로고 이미지 생성 프롬프트에 넣을 것이라," + '\\n'
        + "그림으로 그릴 수 있는 표현이어야 합니다." + '\\n'
        + "- 낱말마다 3~5 단어 안쪽의 영어 구절로 옮깁니다." + '\\n'
        + "- 한국어를 한 글자도 남기지 마세요." + '\\n'
        + f"낱말: {', '.join(keywords)}" + '\\n\\n'
        + '{"themes": ["...", "..."]} 형식의 JSON 으로만 답하세요.'
    )

    try:
        data = _ask_json(ask, api_key, gemini_key)
    except Exception:
        return None

    themes = [str(t).strip() for t in (data.get("themes") or []) if str(t).strip()]
    themes = [t for t in themes if _is_ascii(t)]  # 한국어가 섞여 오면 버린다
    return themes or None


def _ask_json(question: str, openai_key: str, gemini_key: str) -> dict:
    """있는 키로 LLM 을 불러 JSON 을 받는다. 표준 라이브러리만 쓴다."""
    if openai_key:
        body = json.dumps({
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": question}],
            "response_format": {"type": "json_object"},
        }).encode("utf-8")
        request = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions", data=body,
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {openai_key}"}, method="POST")
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return json.loads(payload["choices"][0]["message"]["content"])

    body = json.dumps({
        "contents": [{"parts": [{"text": question}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }).encode("utf-8")
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           "gemini-flash-lite-latest:generateContent")
    request = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json", "x-goog-api-key": gemini_key},
        method="POST")
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))
    parts = payload["candidates"][0]["content"]["parts"]
    return json.loads("".join(part.get("text", "") for part in parts))



def make_prompts(brief: dict, naming: object = None, palette: object = None,
                 count: int = LOGO_COUNT) -> list[str]:
    """이미지 API 에 넣을 프롬프트를 만든다.

    **문장 구조는 언제나 `PROMPT_TEMPLATES` 가 쥔다.** LLM 은 낱말표에 없는
    한국어 키워드를 영어로 옮기는 데만 쓴다.

    예전에는 프롬프트 전체를 LLM 에게 맡겼는데, 모델이 흰 배경·글자 금지·색 이름을
    통째로 지우고 자기 문장으로 다시 써서 로고가 팔레트와 다른 색으로 나왔다.
    """
    brief = brief if isinstance(brief, dict) else {}
    번역 = translate_themes_with_llm(brief)
    if 번역:
        brief = {**brief, "keywords": 번역}
    return build_prompts(brief, naming, palette, count)


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
