"""[2] 네이밍 · 슬로건 · 스토리 — 담당: 박연수

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

# 계약이 요구하는 것 — 이름 3개 이상, 슬로건 3개, 스토리 300자 내외
EXAMPLE = {
    "naming": [
        {"name": "쉼표", "meaning": "문장을 잠시 멈추는 기호에서 따왔습니다"},
        {"name": "여백", "meaning": "비어 있음이 곧 쉼이라는 뜻입니다"},
        {"name": "한 모금", "meaning": "커피 한 모금의 짧은 휴식을 가리킵니다"},
    ],
    "slogans": [
        "잠깐 멈추셔도 됩니다",
        "혼자여도 괜찮은 자리",
        "하루에 한 번, 쉼표",
    ],
    "story": (
        "오피스 상권의 점심시간은 늘 붐빕니다. 자리를 잡기도 전에 다시 일어서야 하고, "
        "혼자 온 사람은 눈치를 봅니다. 이곳은 그 사이를 메우려고 만들었습니다. "
        "테이크아웃이 빠르게 나가되, 앉고 싶은 사람은 오래 앉을 수 있게 자리를 나눴습니다. "
        "혼자 오는 손님이 많은 곳이라 이인석보다 일인석을 늘렸습니다. "
        "바쁜 하루에 문장 하나만큼의 쉼을 두자는 뜻입니다. "
        "커피가 빨리 나오는 곳은 많지만, 잠깐 앉아도 되는 곳은 드뭅니다."
    ),
}

# --- BI 분석 리포트에서 옮긴 규칙 -------------------------------------

NAMING_RULE = (
    "브랜드명 후보를 3개 이상 5개 이하로 만드세요.\n"
    "국내 카페 브랜드는 아래 5가지 유형으로 나뉩니다. 후보마다 다른 유형을 쓰세요.\n"
    "  (1) 문학·인물 차용 — 스타벅스(소설 속 인물), 폴 바셋(실존 바리스타)\n"
    "  (2) 제품 직관형 — 커피빈(콩+찻잎). 무엇을 파는지 이름만으로 전달\n"
    "  (3) 은유·조어형 — 컴포즈(작곡하다), 투썸(둘의 교감)\n"
    "  (4) 속성 강조형 — 메가(대용량). 핵심 강점을 이름에 직접 심음\n"
    "  (5) 지명·역사형 — 이디야(에티오피아 부족), 빽다방(옛 다방 정서)\n"
    "meaning 에는 이름의 뜻과 유래를 한 문장으로 씁니다.\n"
    "이미 널리 쓰이는 유명 브랜드명은 피합니다.\n"
    "가장 좋다고 판단한 후보를 맨 앞에 놓으세요."
)

SLOGAN_RULE = (
    "슬로건을 정확히 3개 만드세요. 셋이 서로 다른 곳을 겨냥해야 합니다.\n"
    "  - 하나는 타깃이 처한 상황을 말합니다\n"
    "  - 하나는 이 브랜드가 주는 감각을 말합니다\n"
    "  - 하나는 브랜드명을 직접 넣어 기억에 남게 합니다\n"
    "각 슬로건은 20자 안쪽으로 짧게 씁니다."
)

STORY_RULE = (
    "브랜드 스토리를 300자 내외(최소 200자)로 쓰세요.\n"
    "세 단으로 구성합니다: (1) 타깃이 겪는 불편 → (2) 브랜드가 내놓은 답 →\n"
    "(3) 그래서 무엇이 달라지는가. 광고 문구가 아니라 설명하는 글로 씁니다."
)

RESPONSE_SHAPE = (
    '{"naming": [{"name": "이름", "meaning": "뜻"}], '
    '"slogans": ["슬로건1", "슬로건2", "슬로건3"], '
    '"story": "300자 내외의 브랜드 스토리"}'
)

# 무료·저가 티어에서 막히는 모델이 있어 앞에서부터 시도하고 되는 것을 쓴다.
MODELS = ("gpt-4o-mini", "gpt-4o")


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

    lines += ["", NAMING_RULE, "", SLOGAN_RULE, "", STORY_RULE, "",
              f"아래 JSON 형식으로만 답하세요. 다른 말은 붙이지 마세요.\n{RESPONSE_SHAPE}"]
    return "\n".join(lines)


def _call_openai(prompt: str, api_key: str) -> dict:
    """OpenAI 를 불러 JSON 을 받아 온다.

    Raises:
        RuntimeError: 모델을 하나도 못 쓴 경우.
    """
    from openai import OpenAI  # 키가 없으면 여기까지 오지 않으므로 안에서 import 한다

    client = OpenAI(api_key=api_key)
    시도 = []
    for model in MODELS:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                timeout=60,
            )
            text = response.choices[0].message.content or ""
            data = json.loads(text)
        except Exception as exc:  # 쿼터·권한·타임아웃·JSON 깨짐을 한데 묶는다
            시도.append(f"{model}={type(exc).__name__}")
            continue  # 이 모델은 못 쓴다. 다음 후보로.

        if isinstance(data, dict):
            return data
        시도.append(f"{model}=객체가 아님")

    raise RuntimeError("사용 가능한 모델이 없습니다 (" + ", ".join(시도) + ")")


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
                naming.append({"name": name, "meaning": str(item.get("meaning") or "").strip()})

    slogans = data.get("slogans")
    if isinstance(slogans, str):
        slogans = [slogans]  # 하나만 준 경우
    slogans = [str(s).strip() for s in (slogans or []) if str(s).strip()]

    return {"naming": naming, "slogans": slogans, "story": str(data.get("story") or "").strip()}


def generate_naming(brief: dict) -> dict:
    """docs/데이터-계약.md 의 [2] 규격대로 dict 를 돌려준다.

    키가 없거나 호출이 실패하면 EXAMPLE 을 돌려준다 — 파이프라인을 멈추지 않는다.
    """
    api_key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if not api_key:
        print("   ℹ️  [2] OPENAI_API_KEY 가 없어 예시 값으로 돌립니다")
        return EXAMPLE

    try:
        result = _normalize(_call_openai(build_prompt(brief), api_key))
    except Exception as exc:
        print(f"   ⚠️  [2] LLM 호출 실패({exc}) — 예시 값으로 대신합니다")
        return EXAMPLE

    # 규격 미달이면 예시가 낫다. 이름 하나짜리 결과로 뒤 단계를 돌릴 수는 없다.
    if len(result["naming"]) < 3 or len(result["slogans"]) < 3:
        print("   ⚠️  [2] 결과가 규격에 못 미쳐 예시 값으로 대신합니다")
        return EXAMPLE
    return result


if __name__ == "__main__":
    # 한글 윈도우 콘솔(cp949)은 '—' 같은 글자에서 죽는다. 혼자 돌려 볼 때를 위한 안전장치.
    import sys
    for _stream in (sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8", errors="replace")

    # 자기 파트만 따로 돌려 볼 때 씁니다.
    #   python step2_naming.py
    from pathlib import Path

    brief_path = Path(__file__).resolve().parent / "samples" / "brief.json"
    sample = json.loads(brief_path.read_text(encoding="utf-8")) if brief_path.exists() else {}
    print(json.dumps(generate_naming(sample), ensure_ascii=False, indent=2))
