"""[3] 컬러 팔레트 — LLM 호출·형식 보정·실패 대응.

진짜 API 는 부르지 않는다. `_pick_provider` 가 돌려주는 호출 함수를 가짜로 바꾼다.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import palette
from brand_result import validate

BRIEF = {
    "industry": "카페",
    "target": "20~30대 직장인",
    "keywords": ["여유", "따뜻함"],
    "tone": "따뜻하고 감성적",
}

NAMING = {
    "naming": [{"name": "쉼표", "english": "Comma", "meaning": "잠깐 멈춤"}],
    "slogans": ["잠깐 멈추셔도 됩니다"],
    "story": "하루에 한 번은 쉼표가 필요합니다. " * 15,
}

ANSWER = {
    "main": {"hex": "#2F4858", "name": "미드나이트 블루", "reason": "차분함을 줍니다"},
    "subs": [
        {"hex": "#F6F4F1", "name": "웜 화이트", "reason": "여백을 만듭니다"},
        {"hex": "#C9A227", "name": "머스터드", "reason": "포인트 색입니다"},
    ],
}


@pytest.fixture
def 가짜LLM(monkeypatch):
    """`_pick_provider` 를 가로채 원하는 응답을 돌려주게 한다."""
    def 설치(응답, *, 키="sk-테스트용가짜키"):
        기록 = []

        def 호출(prompt, _key):
            기록.append(prompt)
            return 응답(prompt) if callable(응답) else 응답

        monkeypatch.setattr(palette, "load_dotenv", lambda *a, **k: False)
        monkeypatch.setattr(palette, "_pick_provider",
                            lambda: ("가짜", 키, 호출))
        return 기록
    return 설치


# --- 실제로 LLM 을 부르는가 -------------------------------------------------

def test_LLM_이_고른_색을_쓴다(가짜LLM):
    """명세 6번은 'LLM API를 호출하여 컬러를 추천받는다' 이다."""
    가짜LLM(ANSWER)
    result = palette.generate_palette(BRIEF, NAMING)

    assert result["main"]["hex"] == "#2F4858"
    assert len(result["subs"]) == 2
    assert result["main"]["hex"] != palette.EXAMPLE["main"]["hex"]


def test_예시_값을_그대로_돌려주지_않는다(가짜LLM):
    """예전에는 하드코딩된 EXAMPLE 이 그대로 나갔다. 브리프가 뭐든 같은 색이었다."""
    가짜LLM(ANSWER)
    result = palette.generate_palette(BRIEF, NAMING)
    assert not result.get("used_example")


def test_브랜드명과_스토리를_프롬프트에_넣는다(가짜LLM):
    """브리프만 넣으면 '카페니까 갈색' 이 나온다. [2] 결과가 들어가야 한다."""
    기록 = 가짜LLM(ANSWER)
    palette.generate_palette(BRIEF, NAMING)

    prompt = 기록[0]
    assert "쉼표" in prompt
    assert "잠깐 멈추셔도 됩니다" in prompt
    assert "하루에 한 번은 쉼표가 필요합니다" in prompt
    assert "카페" in prompt and "여유" in prompt


def test_앞_단계가_없어도_브리프만으로_만든다(가짜LLM):
    """[2] 가 실패하면 naming 이 None 으로 온다. 거기서 죽으면 안 된다."""
    기록 = 가짜LLM(ANSWER)
    result = palette.generate_palette(BRIEF, None)

    assert result["main"]["hex"] == "#2F4858"
    assert "카페" in 기록[0]


# --- 형식 보정 -------------------------------------------------------------

def test_소문자_hex_를_대문자로_고친다(가짜LLM):
    """계약은 '#RRGGBB' 대문자다. 모델이 소문자로 주는 일이 잦다."""
    가짜LLM({"main": {"hex": "#2f4858", "name": "네이비", "reason": "차분함"},
             "subs": [{"hex": "#f6f4f1", "name": "화이트", "reason": "여백"},
                      {"hex": "#c9a227", "name": "머스터드", "reason": "포인트"}]})
    result = palette.generate_palette(BRIEF, NAMING)
    assert result["main"]["hex"] == "#2F4858"
    assert [s["hex"] for s in result["subs"]] == ["#F6F4F1", "#C9A227"]


def test_샵이_빠져도_붙여_준다(가짜LLM):
    가짜LLM({"main": {"hex": "2F4858", "name": "네이비", "reason": "차분함"},
             "subs": [{"hex": "F6F4F1", "name": "화이트", "reason": "여백"},
                      {"hex": "C9A227", "name": "머스터드", "reason": "포인트"}]})
    assert palette.generate_palette(BRIEF, NAMING)["main"]["hex"] == "#2F4858"


def test_서브가_네_개면_세_개까지만_쓴다(가짜LLM):
    """계약은 2~3개다."""
    가짜LLM({"main": ANSWER["main"],
             "subs": ANSWER["subs"] + [
                 {"hex": "#111111", "name": "블랙", "reason": "대비"},
                 {"hex": "#222222", "name": "차콜", "reason": "여분"}]})
    assert len(palette.generate_palette(BRIEF, NAMING)["subs"]) == 3


def test_읽을_수_없는_색은_버린다(가짜LLM):
    """'rgb(...)' 이나 세 자리 축약은 [5] 의 명도 대비 계산을 못 한다."""
    가짜LLM({"main": ANSWER["main"],
             "subs": [{"hex": "rgb(246,244,241)", "name": "화이트", "reason": "여백"},
                      ANSWER["subs"][0], ANSWER["subs"][1]]})
    subs = palette.generate_palette(BRIEF, NAMING)["subs"]
    assert all(s["hex"].startswith("#") for s in subs)
    assert len(subs) == 2


def test_이름이_비면_hex_로_대신한다(가짜LLM):
    가짜LLM({"main": {"hex": "#2F4858", "name": "", "reason": ""},
             "subs": ANSWER["subs"]})
    assert palette.generate_palette(BRIEF, NAMING)["main"]["name"] == "#2F4858"


# --- 실패해도 멈추지 않는가 (명세 9번) --------------------------------------

def test_키가_없으면_예시로_돌린다(monkeypatch):
    monkeypatch.setattr(palette, "load_dotenv", lambda *a, **k: False)
    monkeypatch.setattr(palette, "_pick_provider", lambda: ("", "", None))
    result = palette.generate_palette(BRIEF, NAMING)
    assert result["used_example"] is True
    assert result["main"]["hex"] == palette.EXAMPLE["main"]["hex"]


def test_호출이_실패해도_죽지_않는다(가짜LLM):
    def 터진다(_prompt):
        raise RuntimeError("쿼터 초과")
    가짜LLM(터진다)
    assert palette.generate_palette(BRIEF, NAMING)["used_example"] is True


def test_서브가_모자라면_예시로_대신한다(가짜LLM):
    """색 하나짜리 팔레트로 뒤 단계를 돌릴 수는 없다."""
    가짜LLM({"main": ANSWER["main"], "subs": [ANSWER["subs"][0]]})
    assert palette.generate_palette(BRIEF, NAMING)["used_example"] is True


def test_메인이_없으면_예시로_대신한다(가짜LLM):
    가짜LLM({"subs": ANSWER["subs"]})
    assert palette.generate_palette(BRIEF, NAMING)["used_example"] is True


def test_객체가_아니면_예시로_대신한다(가짜LLM):
    가짜LLM(["#2F4858"])
    assert palette.generate_palette(BRIEF, NAMING)["used_example"] is True


# --- 계약을 지키는가 -------------------------------------------------------

def test_결과가_계약_검증을_통과한다(가짜LLM):
    가짜LLM(ANSWER)
    result = palette.generate_palette(BRIEF, NAMING)
    assert validate.check_palette(result) == []


def test_예시_값도_계약_검증을_통과한다():
    assert validate.check_palette(palette.EXAMPLE) == []


def test_프롬프트가_hex_형식을_못_박는다():
    """이 문장을 빼면 소문자·rgb() 로 오는 비율이 크게 오른다."""
    rule = palette.PALETTE_RULE
    assert "#" in rule and "대문자" in rule
    assert "rgb(" in rule


# --- 메인이 흰 배경에 묻히지 않는가 -----------------------------------------
#
# 로고는 흰 배경 위에 메인 컬러로 그린다. 실측 #C5B29A(2.06:1)로 그린
# 시안이 거의 보이지 않았다.

밝은메인 = {"main": {"hex": "#C5B29A", "name": "부드러운 베이지", "reason": "밝음"},
            "subs": ANSWER["subs"]}


def test_메인이_너무_밝으면_다시_청한다(가짜LLM):
    기록 = 가짜LLM(lambda prompt: ANSWER if "너무 밝습니다" in prompt else 밝은메인)
    result = palette.generate_palette(BRIEF, NAMING)

    assert len(기록) == 2
    assert result["main"]["hex"] == "#2F4858"
    assert "흰 배경" in 기록[1]


def test_다시_청한_것도_밝으면_원래_것을_쓴다(가짜LLM):
    """색은 사람이 판단할 문제다. 버리지 않고 대비 경고만 남긴다."""
    더밝은것 = {"main": {"hex": "#FAF8F5", "name": "아이보리", "reason": "더 밝음"},
                "subs": ANSWER["subs"]}
    가짜LLM(lambda prompt: 더밝은것 if "너무 밝습니다" in prompt else 밝은메인)
    assert palette.generate_palette(BRIEF, NAMING)["main"]["hex"] == "#C5B29A"


def test_메인이_충분히_진하면_다시_청하지_않는다(가짜LLM):
    """멀쩡한 결과에 추가 호출을 하면 토큰 낭비다."""
    기록 = 가짜LLM(ANSWER)
    palette.generate_palette(BRIEF, NAMING)
    assert len(기록) == 1


def test_다시_청하다_실패해도_원래_것을_쓴다(가짜LLM):
    def 응답(prompt):
        if "너무 밝습니다" in prompt:
            raise RuntimeError("쿼터 초과")
        return 밝은메인

    가짜LLM(응답)
    assert palette.generate_palette(BRIEF, NAMING)["main"]["hex"] == "#C5B29A"


def test_프롬프트가_흰_배경_대비를_못_박는다():
    assert "흰 배경" in palette.PALETTE_RULE
    assert palette.MIN_MAIN_CONTRAST >= 3.0
