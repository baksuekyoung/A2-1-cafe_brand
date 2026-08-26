"""[2] 네이밍 · 슬로건 · 스토리

브리프를 받아 브랜드명 후보·슬로건·브랜드 스토리를 생성한다.

프롬프트 규칙은 `국내_카페_브랜드_BI_분석_리포트` 의 분석 결과를 옮긴 것으로,
`NAMING_RULE` · `SLOGAN_RULE` · `STORY_RULE` 세 상수에 정리되어 있다.

## 동작

    .env 에 OPENAI_API_KEY 가 있으면  →  LLM 호출
    없거나 호출이 실패하면            →  EXAMPLE 로 대체 (파이프라인은 중단하지 않는다)

두 번째가 중요하다. API 키가 막히거나 쿼터가 소진돼도 전체 실행이 멈추지 않는다.
어느 쪽을 썼는지는 `run_report.md` 에 남는다.
"""

from __future__ import annotations

import json
import os
import re
import urllib.request
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # python-dotenv 를 안 깔았어도 돌아가야 한다
    def load_dotenv(*_args, **_kwargs) -> bool:
        return False

ENV_PATH = Path(__file__).resolve().parent / ".env"

# `docs/참고자료/sample_output.json` 의 내용에 보너스 항목(영문 표기·경쟁사 분석)을 더한 것.
EXAMPLE = {
        "naming": [
            {
                "name": "온기(溫氣)",
                "english": "Ongi",
                "reading": "OWN-gee",
                "meaning": "따뜻한 기운이라는 뜻으로, 커피 한 잔이 주는 온기와 사람 사이의 따뜻함을 동시에 담았습니다."
            },
            {
                "name": "쉼표",
                "english": "Comma",
                "reading": "COM-ma",
                "meaning": "바쁜 일상 속 잠깐 멈추는 순간을 뜻합니다. 문장 속 쉼표처럼, 삶의 리듬을 조율하는 공간을 표현합니다."
            },
            {
                "name": "모닥",
                "english": "Modak",
                "reading": "MO-dak",
                "meaning": "모닥불의 줄임말로, 작지만 확실한 따뜻함을 주는 공간이라는 의미를 담았습니다."
            },
            {
                "name": "한뼘",
                "english": "Hanppyeom",
                "reading": "HAN-byeom",
                "meaning": "아주 작은 여유라도 충분하다는 뜻입니다. 바쁜 하루 중 한 뼘만큼의 쉬어가는 시간을 선물합니다."
            },
            {
                "name": "노을목",
                "english": "Noeulmok",
                "reading": "NO-eul-mok",
                "meaning": "노을이 지는 시간, 하루를 마무리하며 잠시 머무는 장소라는 의미입니다."
            }
        ],
        "slogans": [
            "오늘 하루, 여기서 잠깐 쉬어가요.",
            "한 잔의 온기가 하루를 바꿉니다.",
            "당신의 일상에 쉼표 하나를 더해드립니다."
        ],
        "story": "온기는 '커피 한 잔이 사람을 연결한다'는 믿음에서 시작되었습니다. 빠르게 흘러가는 일상 속에서 우리는 종종 멈추는 법을 잊습니다. 점심시간의 카페는 늘 붐비고, 혼자 온 사람은 자리를 잡기도 전에 눈치를 봅니다. 온기는 그 잠깐의 멈춤이 얼마나 소중한지 알기에, 누구나 편안하게 앉아 숨을 고를 수 있는 공간을 만들었습니다. 빨리 나가는 한 잔과 오래 앉는 한 자리를 따로 두고, 혼자 온 손님을 위한 일인석을 넉넉히 놓았습니다. 좋은 원두, 정성스러운 한 잔, 그리고 따뜻한 공간. 온기는 오늘도 당신의 하루 한가운데 조용히 자리하며, 이 도시에서 가장 편하게 쉬어 갈 수 있는 이름이 되려 합니다.",
        "competitors": [
            {
                "competitor": "블루보틀",
                "position": "느린 추출과 절제된 공간으로 커피 자체에 집중하게 하는 스페셜티 브랜드입니다.",
                "differentiation": "우리는 커피의 완성도보다 '앉아 있어도 되는 시간'을 팔아, 혼자 온 직장인이 눈치 보지 않는 자리를 만듭니다."
            },
            {
                "competitor": "스타벅스",
                "position": "어디서나 같은 맛과 빠른 회전으로 도시의 기본값이 된 대형 체인입니다.",
                "differentiation": "우리는 표준화 대신 동네의 결을 남겨, '일상의 쉼표'라는 키워드를 매장 구성과 좌석 배치로 그대로 옮깁니다."
            }
        ]
    }


# --- BI 분석 리포트에서 옮긴 규칙 -------------------------------------

NAMING_RULE = (
    "브랜드명 후보를 **4개 이상 5개 이하**로 만드세요.\n"
    "세 개만 내면 고를 여지가 없습니다. 네 개를 채우고, 더 낼 수 있으면 다섯 개까지 냅니다.\n"
    "\n"
    "## 반드시 피할 것 — 이걸 어기면 다시 만들어야 합니다\n"
    "\n"
    "**(가) 업종 이름을 뒤에 붙이지 마세요.**\n"
    "  ❌ 여유카페 · 온기카페 · 쉼표다방 · 감성커피 · 여유다방\n"
    "  카페·커피·다방·하우스·랩·스튜디오 같은 낱말을 이름에 넣지 않습니다.\n"
    "  스타벅스도 이디야도 업종을 이름에 넣지 않았습니다. 간판이 업종을 말해 줍니다.\n"
    "\n"
    "**(나) 브리프 키워드를 그대로 이름으로 쓰지 마세요.**\n"
    "  키워드가 '여유' 라고 '여유' 나 '여유로운' 을 이름으로 내면 안 됩니다.\n"
    "  키워드는 **느낌의 방향**이지 이름 후보가 아닙니다.\n"
    "  키워드가 떠올리게 하는 **구체적인 사물·장면·순간**으로 한 번 옮겨서 지으세요.\n"
    "  예: '여유' → 창가 자리, 오후 세 시, 접어 둔 책갈피, 식은 커피\n"
    "\n"
    "**(다) 서로 닮은 후보를 늘어놓지 마세요.**\n"
    "  네 개가 모두 두 글자 순우리말이거나, 모두 '○○+업종' 이면 후보가 하나인 셈입니다.\n"
    "\n"
    "## 후보마다 다른 유형으로\n"
    "\n"
    "국내 카페 브랜드는 아래 5가지 유형으로 나뉩니다. **후보마다 다른 유형을 쓰세요.**\n"
    "  (1) 문학·인물 차용 — 스타벅스(소설 속 인물), 폴 바셋(실존 바리스타)\n"
    "  (2) 제품 직관형 — 커피빈(콩+찻잎). 무엇을 파는지 이름만으로 전달\n"
    "  (3) 은유·조어형 — 컴포즈(작곡하다), 투썸(둘의 교감)\n"
    "  (4) 속성 강조형 — 메가(대용량). 핵심 강점을 이름에 직접 심음\n"
    "  (5) 지명·역사형 — 이디야(에티오피아 부족), 빽다방(옛 다방 정서)\n"
    "\n"
    "`type` 에 그 후보가 몇 번 유형인지 숫자로 적으세요. 숫자가 겹치면 안 됩니다.\n"
    "\n"
    "## 그 밖에\n"
    "\n"
    "meaning 에는 이름의 뜻과 유래를 한 문장으로 씁니다.\n"
    "  '따뜻함을 뜻합니다' 처럼 낱말을 되풀이하지 말고, **어디서 가져왔는지**를 밝히세요.\n"
    "이미 널리 쓰이는 유명 브랜드명은 피합니다.\n"
    "부르기 쉽게 2~4음절로 짓습니다. 다섯 음절이 넘으면 간판에서 읽히지 않습니다.\n"
    "가장 좋다고 판단한 후보를 맨 앞에 놓으세요."
)

# 위 규칙을 어겼는지는 `validate._check_distinctiveness` 가 본다.
# 걸러 내지는 않고 run_report.md 에 적는다 — 채택은 사람이 판단할 문제다.

# 보너스 — 다국어 네이밍 지원. 한글 이름마다 영문 표기를 함께 만든다.
MULTILINGUAL_RULE = (
    "후보마다 **한글 이름과 영문 표기를 함께** 만드세요. 둘 다 반드시 채웁니다.\n"
    "  - name    : 한글 이름\n"
    "  - english : 같은 이름의 영문 표기\n"
    "  - reading : 영문 표기를 어떻게 읽는지 (예: OWN-gee)\n"
    "영문 표기는 간판·도메인·SNS 계정에 그대로 쓸 수 있어야 합니다.\n"
    "  - 소리 나는 대로 옮기거나(온기 → Ongi), 뜻이 통하는 영어 낱말로 짓습니다(쉼표 → Comma).\n"
    "  - 12자 안쪽, 알파벳만 씁니다. 숫자·기호·띄어쓰기를 넣지 마세요.\n"
    "  - 영어권 사람이 읽었을 때 발음하기 쉬워야 합니다.\n"
    "  - 다른 뜻으로 읽히지 않는지 확인하세요 (예: 한글 '모닥' 을 Modak 으로 쓰면 무난하지만,\n"
    "    Mock 처럼 들리는 표기는 피합니다).\n"
    "  - 후보끼리 영문 표기가 겹치지 않게 합니다."
)

SLOGAN_RULE = (
    "슬로건을 정확히 3개 만드세요. 셋이 서로 다른 곳을 겨냥해야 합니다.\n"
    "  - 하나는 타깃이 처한 상황을 말합니다\n"
    "  - 하나는 이 브랜드가 주는 감각을 말합니다\n"
    "  - 하나는 브랜드명을 직접 넣어 기억에 남게 합니다\n"
    "각 슬로건은 20자 안쪽으로 짧게 씁니다."
)

STORY_RULE = (
    "브랜드 스토리를 **280자에서 320자 사이**로 쓰세요. 이 범위를 반드시 지킵니다.\n"
    "짧게 쓰면 규격 미달로 잡힙니다. 다 쓴 뒤 글자 수를 세어 보고 모자라면 늘리세요.\n"
    "명세가 요구하는 세 가지를 모두 담습니다.\n"
    "  (1) 탄생 배경 — 타깃이 겪는 불편에서 시작해 왜 이 브랜드를 만들었는가\n"
    "  (2) 철학 — 그래서 무엇을 지키기로 했는가\n"
    "  (3) 비전 — 앞으로 어떤 자리가 되려 하는가\n"
    "세 가지에 각각 두세 문장씩 쓰면 자연스럽게 300자가 됩니다.\n"
    "광고 문구가 아니라 설명하는 글로 씁니다."
)

# 보너스 — 입력된 경쟁사를 분석해 차별화 포인트를 제안한다.
COMPETITOR_RULE = (
    "브리프에 적힌 경쟁사를 하나씩 짚어 차별화 포인트를 제안하세요.\n"
    "경쟁사마다 아래 세 가지를 씁니다.\n"
    "  - competitor: 경쟁사 이름\n"
    "  - position: 그 브랜드가 시장에서 차지한 자리를 한 문장으로\n"
    "  - differentiation: 우리가 다르게 갈 지점을 한 문장으로. 막연한 말 대신\n"
    "    이 브리프의 타깃·키워드에 근거해 구체적으로 씁니다.\n"
    "경쟁사가 없으면 competitors 를 빈 배열로 두세요."
)

RESPONSE_SHAPE = (
    '{"naming": [{"name": "한글 이름", "english": "영문 표기", '
    '"reading": "영문 읽는 법", "meaning": "뜻과 유래", "type": 유형번호}], '
    '"slogans": ["슬로건1", "슬로건2", "슬로건3"], '
    '"story": "300자 내외의 브랜드 스토리", '
    '"competitors": [{"competitor": "경쟁사", "position": "시장에서의 자리", '
    '"differentiation": "우리가 다르게 갈 지점"}]}'
)

# 계약(docs/데이터-계약.md)이 정한 스토리 최소 길이. validate.py 와 같은 값이다.
MIN_STORY_CHARS = 200

# 명세는 "300자 내외"를 요구한다. 계약 최소치(200)만 넘으면 통과시키면
# 실측 204자 같은 결과가 그대로 나가므로, 다시 청하는 기준은 따로 둔다.
STORY_TARGET_CHARS = 280
STORY_RETRIES = 2

# 무료·저가 티어에서 막히는 모델이 있어 앞에서부터 시도하고 되는 것을 쓴다.
OPENAI_MODELS = ("gpt-4o-mini", "gpt-4o")

# 코디세이 공개 API — 소속 기관 키로 정산되고 본인 월 한도에서 차감된다.
# 차감 배수가 낮은 것부터 시도한다 (gpt-5-mini·gemini 계열 0.5, gpt-5.4 는 1).
CODYSSEY_BASE_URL = "https://copa.codyssey.kr"
CODYSSEY_MODELS = ("gpt-5-mini", "gemini-3-flash", "gpt-5.4-mini", "gpt-5.4")
GEMINI_MODELS = ("gemini-flash-lite-latest", "gemini-flash-latest", "gemini-2.5-flash")

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)
OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"


def build_prompt(brief: dict) -> str:
    """브리프를 프롬프트에 그대로 녹인다.

    업종·타깃·키워드·톤을 안 넣으면 "어떤 카페든 쓸 수 있는" 결과가 나온다.
    가이드 체크포인트가 "결과가 너무 일반적이지 않고 구체적인가" 이다.
    """
    keywords = ", ".join(str(k) for k in brief.get("keywords") or [])
    competitors = ", ".join(str(c) for c in brief.get("competitors") or [])

    lines = [
        "당신은 브랜드 네이밍 전문가입니다. 아래 브리프에 맞는 브랜드 아이덴티티를 만드세요.",
        "",
        f"업종: {brief.get('industry', '')}",
        f"타깃: {brief.get('target', '')}",
        f"키워드: {keywords}",
    ]
    if brief.get("tone"):
        lines.append(f"톤앤매너: {brief['tone']}")
    if competitors:
        lines.append(f"참고 경쟁사: {competitors} (이들과 겹치지 않게 차별화하세요)")
    if brief.get("notes"):
        lines.append(f"추가 요청: {brief['notes']}")

    lines += ["", NAMING_RULE, "", MULTILINGUAL_RULE, "", SLOGAN_RULE, "",
              STORY_RULE, "", COMPETITOR_RULE, "",
              f"아래 JSON 형식으로만 답하세요. 다른 말은 붙이지 마세요.\n{RESPONSE_SHAPE}"]
    return "\n".join(lines)


def _call_gemini(prompt: str, api_key: str) -> dict:
    """Gemini 를 불러 JSON 을 받아 온다.

    `openai` 패키지 없이 표준 라이브러리만으로 부른다.

    Raises:
        RuntimeError: 모델을 하나도 못 쓴 경우.
    """
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }).encode("utf-8")

    시도 = []
    for model in GEMINI_MODELS:
        request = urllib.request.Request(
            GEMINI_URL.format(model=model),
            data=body,
            headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                payload = json.loads(response.read().decode("utf-8"))
            parts = payload["candidates"][0]["content"]["parts"]
            data = json.loads("".join(p.get("text", "") for p in parts))
        except Exception as exc:  # 쿼터·권한·안전필터·JSON 깨짐을 한데 묶는다
            시도.append(f"{model}={type(exc).__name__}")
            continue  # 이 모델은 못 쓴다. 다음 후보로.

        if isinstance(data, dict):
            return data
        시도.append(f"{model}=객체가 아님")

    raise RuntimeError("사용 가능한 Gemini 모델이 없습니다 (" + ", ".join(시도) + ")")


def _call_openai(prompt: str, api_key: str) -> dict:
    """OpenAI 를 불러 JSON 을 받아 온다.

    `openai` 패키지를 쓰지 않고 표준 라이브러리로 부른다.
    설치 환경에 따라 그 패키지가 import 조차 안 되는 일이 있어서다
    (실제로 `_ctypes` DLL 오류로 import 가 실패하는 환경을 만났다).
    HTTP 요청 한 번이면 되는 일에 무거운 의존성을 두지 않는다.

    Raises:
        RuntimeError: 모델을 하나도 못 쓴 경우.
    """
    return _call_chat_api(prompt, api_key, OPENAI_CHAT_URL, OPENAI_MODELS,
                          json_mode=True, 이름="OpenAI")


def _call_codyssey(prompt: str, api_key: str) -> dict:
    """코디세이 공개 API 를 부른다. OpenAI 와 같은 규격이라 호출부를 공유한다.

    다른 점은 하나뿐이다 — `response_format` 을 받지 않는다.
    보내면 HTTP 400 `unsupported_feature` 가 온다 (실측).
    그래서 JSON 은 프롬프트로만 요구하고, 울타리는 벗겨 낸다.
    """
    return _call_chat_api(prompt, api_key, _codyssey_chat_url(), CODYSSEY_MODELS,
                          json_mode=False, 이름="코디세이")


def _codyssey_chat_url() -> str:
    base = (os.environ.get("CODYSSEY_BASE_URL") or CODYSSEY_BASE_URL).rstrip("/")
    return f"{base}/v1/chat/completions"


def _strip_fence(text: str) -> str:
    """```json ... ``` 울타리를 벗긴다.

    JSON 강제 모드를 못 쓰는 공급자는 답을 코드블록으로 감싸 주는 일이 있다.
    """
    text = (text or "").strip()
    if not text.startswith("```"):
        return text
    text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
    return re.sub(r"\s*```$", "", text).strip()


def _call_chat_api(prompt: str, api_key: str, url: str, models,
                   *, json_mode: bool, 이름: str) -> dict:
    """OpenAI 규격 채팅 API 를 부른다. 되는 모델이 나올 때까지 앞에서부터 시도한다.

    Raises:
        RuntimeError: 모델을 하나도 못 쓴 경우.
    """
    기본 = {"messages": [{"role": "user", "content": prompt}]}
    if json_mode:
        기본["response_format"] = {"type": "json_object"}

    시도 = []
    for model in models:
        payload = dict(기본, model=model)
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {api_key}"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                answer = json.loads(response.read().decode("utf-8"))
            data = json.loads(_strip_fence(answer["choices"][0]["message"]["content"]))
        except Exception as exc:  # 쿼터·권한·타임아웃·JSON 깨짐을 한데 묶는다
            시도.append(f"{model}={type(exc).__name__}")
            continue  # 이 모델은 못 쓴다. 다음 후보로.

        if isinstance(data, dict):
            return data
        시도.append(f"{model}=객체가 아님")

    raise RuntimeError(f"사용 가능한 {이름} 모델이 없습니다 (" + ", ".join(시도) + ")")


def _normalize(data: dict) -> dict:
    """받은 것을 계약 형식으로 다듬는다.

    모델은 규격을 자주 어긴다 — 이름을 문자열로만 주거나, 슬로건을 하나로 합치거나.
    여기서 고칠 수 있는 것은 고치고, 못 고치는 것은 [5] 검증이 잡게 그대로 둔다.
    """
    naming = []
    for item in data.get("naming") or []:
        if isinstance(item, str):
            naming.append({"name": item.strip(), "meaning": ""})
        elif isinstance(item, dict):
            name = str(item.get("name") or item.get("korean") or "").strip()
            if name:
                naming.append({
                    "name": name,
                    # 보너스 — 다국어 네이밍. 한글 이름마다 영문 표기를 함께 낸다.
                    "english": str(item.get("english") or item.get("en") or "").strip(),
                    "reading": str(item.get("reading") or "").strip(),
                    "meaning": str(item.get("meaning") or "").strip(),
                    # 어느 유형으로 지었는지. 겹치면 후보가 서로 닮았다는 뜻이다.
                    "type": str(item.get("type") or "").strip(),
                })

    slogans = data.get("slogans")
    if isinstance(slogans, str):
        slogans = [slogans]  # 하나만 준 경우
    slogans = [str(s).strip() for s in (slogans or []) if str(s).strip()]

    # 보너스 — 경쟁사 분석. 셋 다 채워진 항목만 남긴다.
    competitors = []
    for item in data.get("competitors") or []:
        if not isinstance(item, dict):
            continue
        entry = {key: str(item.get(key) or "").strip()
                 for key in ("competitor", "position", "differentiation")}
        if entry["competitor"] and entry["differentiation"]:
            competitors.append(entry)

    return {
        "naming": naming,
        "slogans": slogans,
        "story": str(data.get("story") or "").strip(),
        "competitors": competitors,
    }


def _pick_provider():
    """쓸 수 있는 LLM 을 고른다. 앞에서부터 키가 있는 것을 쓴다.

    코디세이가 맨 앞이다. 소속 기관 키로 정산되므로 개인 결제분을 쓰지 않는다.
    한도가 떨어지거나 키가 없으면 뒤 공급자로 이어진다.
    명세는 'LLM API' 라고만 요구하므로 어느 쪽이든 된다.

    Returns:
        (공급자 이름, 키, 호출 함수). 키가 하나도 없으면 키 자리가 빈 문자열.
    """
    후보 = (
        ("코디세이", "CODYSSEY_OPENAI_KEY", _call_codyssey),
        ("OpenAI", "OPENAI_API_KEY", _call_openai),
        ("Gemini", "GEMINI_API_KEY", _call_gemini),
    )
    for 이름, 환경변수, 호출 in 후보:
        키 = (os.environ.get(환경변수) or "").strip()
        if 키:
            return 이름, 키, 호출

    return "", "", _call_openai


def generate_naming(brief: dict) -> dict:
    """docs/데이터-계약.md 의 [2] 규격대로 dict 를 돌려준다.

    키가 없거나 호출이 실패하면 EXAMPLE 을 돌려준다 — 파이프라인을 멈추지 않는다.
    """
    # .env 를 먼저 읽는다. 이걸 빼면 키를 .env 에만 넣은 사람은 계속 예시 값으로 돈다.
    # 경로를 직접 준다 — 인자 없이 부르면 다른 폴더에서 실행했을 때 못 찾는다.
    try:
        load_dotenv(ENV_PATH)
    except Exception:
        pass  # .env 를 못 읽어도 환경변수로 넣었을 수 있다

    provider, api_key, call = _pick_provider()
    if not api_key:
        print("   ℹ️  [2] API 키가 없어 예시 값으로 돌립니다"
              " (.env 에 OPENAI_API_KEY 또는 GEMINI_API_KEY)")
        return dict(EXAMPLE, used_example=True)

    try:
        result = _normalize(call(build_prompt(brief), api_key))
    except Exception as exc:
        print(f"   ⚠️  [2] {provider} 호출 실패({exc}) — 예시 값으로 대신합니다")
        return dict(EXAMPLE, used_example=True)
    print(f"   🤖 [2] {provider} 로 생성했습니다")

    # 규격 미달이면 예시가 낫다. 이름 하나짜리 결과로 뒤 단계를 돌릴 수는 없다.
    if len(result["naming"]) < 3 or len(result["slogans"]) < 3:
        print("   ⚠️  [2] 결과가 규격에 못 미쳐 예시 값으로 대신합니다")
        return dict(EXAMPLE, used_example=True)

    # 스토리만 짧게 오는 일이 잦다 — "280~320자" 를 프롬프트에 못 박아도
    # 실측 178·193·194자로 왔다. 그럴 때 스토리만 한 번 다시 청한다.
    # 전체를 다시 돌리는 것보다 훨씬 싸고, 두 번째도 짧으면 그냥 받아들인다
    # (규격 미달은 run_report.md 에 기록되므로 사람이 보고 판단한다).
    if len(result["story"]) < STORY_TARGET_CHARS:
        result["story"] = _retry_story(result["story"], brief, api_key, call)
    return result


def _retry_story(short_story: str, brief: dict, api_key: str, call) -> str:
    """짧게 온 스토리를 다시 청한다. 끝내 못 늘리면 가장 긴 것을 돌려준다."""
    best = short_story
    for _ in range(STORY_RETRIES):
        ask = (_ask_from_scratch(brief) if not best else _ask_longer(best, brief))
        try:
            longer = str(call(ask, api_key).get("story") or "").strip()
        except Exception:
            break
        if len(longer) > len(best):
            print(f"   🔁 [2] 스토리를 다시 청했습니다 ({len(best)} -> {len(longer)}자)")
            best = longer
        if len(best) >= STORY_TARGET_CHARS:
            break
    return best


def _ask_longer(story: str, brief: dict) -> str:
    """있는 스토리를 늘려 달라고 청한다."""
    return (
        f"아래 브랜드 스토리는 {len(story)}자로 너무 짧습니다.\n"
        "내용과 어조는 유지한 채 **280자에서 320자 사이**로 늘려 다시 쓰세요.\n"
        "탄생 배경, 철학, 비전 세 가지가 모두 담겨야 합니다.\n"
        "쓴 뒤 공백까지 세어 보고 280자에 못 미치면 더 채우세요.\n\n"
        f"업종: {brief.get('industry', '')} / 타깃: {brief.get('target', '')}\n\n"
        f"원래 스토리:\n{story}\n\n"
        '{"story": "다시 쓴 스토리"} 형식의 JSON 으로만 답하세요.'
    )


def _ask_from_scratch(brief: dict) -> str:
    """스토리가 아예 비어 왔을 때 새로 써 달라고 청한다.

    후보 개수를 늘린 뒤 `story` 가 빈 문자열로 오는 일을 실제로 만났다.
    그때 "0자짜리를 늘려 쓰라" 고 청하면 늘릴 원문이 없어 말이 되지 않는다.
    """
    keywords = ", ".join(str(k) for k in brief.get("keywords") or [])
    lines = [
        "아래 브랜드의 스토리를 **280자에서 320자 사이**로 쓰세요.",
        "탄생 배경, 철학, 비전 세 가지가 모두 담겨야 합니다.",
        "쓴 뒤 공백까지 세어 보고 280자에 못 미치면 더 채우세요.",
        "",
        f"업종: {brief.get('industry', '')}",
        f"타깃: {brief.get('target', '')}",
        f"키워드: {keywords}",
    ]
    if brief.get("tone"):
        lines.append(f"톤앤매너: {brief['tone']}")
    lines += ["", '{"story": "브랜드 스토리"} 형식의 JSON 으로만 답하세요.']
    return "\n".join(lines)


if __name__ == "__main__":
    # 한글 윈도우 콘솔(cp949)은 '—' 같은 글자에서 죽는다. 혼자 돌려 볼 때를 위한 안전장치.
    import sys
    for _stream in (sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8", errors="replace")

    # 자기 파트만 따로 돌려 볼 때 씁니다.
    #   python naming.py
    from pathlib import Path

    brief_path = Path(__file__).resolve().parent / "samples" / "brief.json"
    sample = json.loads(brief_path.read_text(encoding="utf-8")) if brief_path.exists() else {}
    print(json.dumps(generate_naming(sample), ensure_ascii=False, indent=2))
