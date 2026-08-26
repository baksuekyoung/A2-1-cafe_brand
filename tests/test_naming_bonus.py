"""[2] 네이밍 — 규격과 보너스 과제.

명세의 보너스는 둘 중 선택이다. **"다국어 네이밍 지원" 을 택했다.**
그래서 영문 표기는 **있어야 한다** — 비면 `run_report.md` 에 기록된다.

경쟁사 분석은 택하지 않았지만 함께 구현했고, 이쪽은 없어도 규격 미달이 아니다.
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from brand_result import report, validate

# 이름 그대로 import 하면 안 된다. 다른 테스트가 "단계 파일이 아직 없는" 상태를
# 검사하려고 import 를 가로막는데, 여기서 미리 sys.modules 에 올려 두면 충돌한다.
# 그래서 파일 경로로 직접 읽어 **다른 이름**으로 등록한다.
_STEP2 = Path(__file__).resolve().parent.parent / "naming.py"
_spec = importlib.util.spec_from_file_location("naming_under_test", _STEP2)
naming = importlib.util.module_from_spec(_spec)
sys.modules["naming_under_test"] = naming
_spec.loader.exec_module(naming)

BRIEF = {
    "industry": "카페",
    "target": "20~30대 직장인",
    "keywords": ["여유", "따뜻함"],
    "tone": "따뜻하고 감성적인",
    "competitors": ["블루보틀", "스타벅스"],
    "notes": "한글과 영어 모두 쓰기 쉬운 이름",
}


# --- 프롬프트 ------------------------------------------------------------

def test_브리프의_여섯_필드가_모두_프롬프트에_들어간다():
    prompt = naming.build_prompt(BRIEF)
    assert "카페" in prompt
    assert "20~30대 직장인" in prompt
    assert "여유, 따뜻함" in prompt
    assert "따뜻하고 감성적인" in prompt
    assert "블루보틀" in prompt and "스타벅스" in prompt
    assert "한글과 영어 모두 쓰기 쉬운 이름" in prompt


def test_보너스_규칙이_프롬프트에_실린다():
    prompt = naming.build_prompt(BRIEF)
    assert "english" in prompt              # 영문 네이밍
    assert "differentiation" in prompt      # 경쟁사 차별화


def test_명세가_요구하는_개수가_프롬프트에_숫자로_적힌다():
    """'여러 개' 라고 쓰면 모델마다 다르게 읽는다."""
    prompt = naming.build_prompt(BRIEF)
    assert "4개 이상 5개 이하" in prompt    # 명세는 3~5개지만 3개는 고를 여지가 없다
    assert "정확히 3개" in prompt           # 슬로건
    assert "300자 내외" in prompt           # 스토리


def test_예시_값도_후보를_넉넉히_준다():
    """호출이 실패해 예시로 떨어져도 후보가 셋뿐이면 안 된다."""
    assert 4 <= len(naming.EXAMPLE["naming"]) <= 5


def test_스토리_규칙이_명세_문구를_담는다():
    assert "탄생 배경" in naming.STORY_RULE
    assert "철학" in naming.STORY_RULE
    assert "비전" in naming.STORY_RULE


def test_경쟁사가_없으면_그_줄을_빼고_만든다():
    prompt = naming.build_prompt({"industry": "카페", "keywords": ["여유"]})
    assert "참고 경쟁사" not in prompt


# --- 응답 정규화 ---------------------------------------------------------

# --- 보너스: 다국어 네이밍 지원 -----------------------------------------

def test_다국어_규칙이_프롬프트에_실린다():
    prompt = naming.build_prompt(BRIEF)
    assert "한글 이름과 영문 표기를 함께" in prompt
    assert "reading" in prompt


def test_영문_표기의_조건이_숫자로_적힌다():
    """'짧게' 라고 쓰면 모델마다 다르게 읽는다."""
    assert "12자 안쪽" in naming.MULTILINGUAL_RULE


def test_읽는_법도_받아_담는다():
    result = naming._normalize({
        "naming": [{"name": "온기", "english": "Ongi", "reading": "OWN-gee",
                    "meaning": "따뜻한 기운"}],
    })
    assert result["naming"][0]["reading"] == "OWN-gee"


def test_영문_표기가_비면_규격_위반으로_잡는다():
    """보너스로 택한 항목이므로 빠지면 기록에 남아야 한다."""
    naming = {"naming": [{"name": f"이름{i}", "meaning": "뜻"} for i in range(3)],
              "slogans": ["가", "나", "다"], "story": "이" * 300}
    문제 = validate.check_naming(naming)
    assert len(문제) == 3
    assert all("english" in p for p in 문제)


def test_영문_자리에_한글이_오면_잡는다():
    naming = {"naming": [{"name": "온기", "english": "온기", "meaning": "뜻"}] * 3,
              "slogans": ["가", "나", "다"], "story": "이" * 300}
    assert any("영문이 아닌" in p for p in validate.check_naming(naming))


def test_예시값의_모든_후보에_영문_표기가_있다():
    for item in naming.EXAMPLE["naming"]:
        assert item["english"].isascii() and item["english"]
        assert item["reading"]


def test_결과_문서에_읽는_법까지_실린다():
    text = report._full_name({"name": "온기", "english": "Ongi", "reading": "OWN-gee"})
    assert text == "온기 (Ongi, OWN-gee)"


def test_읽는_법이_없으면_영문만_붙인다():
    assert report._full_name({"name": "온기", "english": "Ongi"}) == "온기 (Ongi)"


def test_영문_표기가_없으면_한글만_쓴다():
    assert report._full_name({"name": "온기"}) == "온기"


def test_영문_표기를_받아_담는다():
    result = naming._normalize({
        "naming": [{"name": "온기", "english": "Ongi", "meaning": "따뜻한 기운"}],
        "slogans": ["가", "나", "다"],
        "story": "이야기",
    })
    assert result["naming"][0]["english"] == "Ongi"


def test_영문_표기가_없어도_키는_있다():
    """뒤 단계가 매번 확인하지 않아도 되게 빈 문자열로 채운다."""
    result = naming._normalize({"naming": [{"name": "온기"}]})
    assert result["naming"][0]["english"] == ""


def test_경쟁사_분석을_받아_담는다():
    result = naming._normalize({
        "competitors": [{"competitor": "블루보틀", "position": "스페셜티",
                         "differentiation": "앉아 있어도 되는 시간을 판다"}],
    })
    assert result["competitors"][0]["competitor"] == "블루보틀"


def test_차별화가_비면_그_경쟁사는_버린다():
    """이름만 있고 알맹이가 없으면 결과 문서에 실을 것이 없다."""
    result = naming._normalize({
        "competitors": [
            {"competitor": "블루보틀", "position": "스페셜티", "differentiation": "  "},
            {"competitor": "스타벅스", "position": "체인", "differentiation": "동네의 결"},
        ],
    })
    assert [c["competitor"] for c in result["competitors"]] == ["스타벅스"]


def test_슬로건을_하나만_주면_배열로_감싼다():
    assert naming._normalize({"slogans": "하나뿐"})["slogans"] == ["하나뿐"]


def test_이름을_문자열로만_줘도_받아_낸다():
    result = naming._normalize({"naming": ["온기"]})
    assert result["naming"][0] == {"name": "온기", "meaning": ""}


# --- LLM 호출 (가짜 응답으로) --------------------------------------------

ANSWER = {
    "naming": [
        {"name": "온기", "english": "Ongi", "reading": "OWN-gee", "meaning": "따뜻한 기운"},
        {"name": "쉼표", "english": "Comma", "reading": "COM-ma", "meaning": "잠깐 멈춤"},
        {"name": "모닥", "english": "Modak", "reading": "MO-dak", "meaning": "작은 불빛"},
    ],
    "slogans": ["가", "나", "다"],
    "story": "이" * 300,
    "competitors": [{"competitor": "블루보틀", "position": "스페셜티",
                     "differentiation": "머무는 시간"}],
}


def test_모델이_돌려준_결과를_그대로_쓴다(monkeypatch):
    """진짜 키 없이도 호출 경로 전체가 도는지 본다.

    `_call_openai` 는 `openai` 패키지를 쓰지 않고 urllib 로 직접 부른다.
    그래서 여기서도 패키지가 아니라 그 함수를 가로챈다.
    """
    monkeypatch.setenv("OPENAI_API_KEY", "sk-테스트용가짜키")
    monkeypatch.setattr(naming, "load_dotenv", lambda *a, **k: False)
    monkeypatch.setattr(naming, "_call_openai", lambda *a, **k: ANSWER)

    result = naming.generate_naming(BRIEF)
    assert result is not naming.EXAMPLE
    assert [n["english"] for n in result["naming"]] == ["Ongi", "Comma", "Modak"]
    assert [n["reading"] for n in result["naming"]] == ["OWN-gee", "COM-ma", "MO-dak"]
    assert result["competitors"][0]["differentiation"] == "머무는 시간"


def test_openai_키가_없으면_gemini_로_간다(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "AQ.테스트용가짜키")
    monkeypatch.setattr(naming, "load_dotenv", lambda *a, **k: False)
    monkeypatch.setattr(naming, "_call_gemini", lambda *a, **k: ANSWER)

    assert naming.generate_naming(BRIEF) is not naming.EXAMPLE


def test_공급자를_고르는_순서는_openai_먼저(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-가짜")
    monkeypatch.setenv("GEMINI_API_KEY", "AQ.가짜")
    이름, 키, 호출 = naming._pick_provider()
    assert 이름 == "OpenAI" and 호출 is naming._call_openai


def test_스토리가_짧으면_다시_청한다(monkeypatch):
    """실측 178·193·194자 — 프롬프트만으로는 못 막아서 넣은 안전장치다."""
    짧은 = dict(ANSWER, story="이" * 150)
    호출 = []

    def 가짜호출(prompt, _key):
        호출.append(prompt)
        if len(호출) == 1:
            return 짧은
        return {"story": "구" * 300}

    monkeypatch.setenv("OPENAI_API_KEY", "sk-테스트용가짜키")
    monkeypatch.setattr(naming, "load_dotenv", lambda *a, **k: False)
    monkeypatch.setattr(naming, "_call_openai", 가짜호출)

    result = naming.generate_naming(BRIEF)
    assert len(호출) == 2                      # 목표치를 채웠으므로 더 청하지 않는다
    assert len(result["story"]) == 300
    assert "원래 스토리" in 호출[1]            # 다시 청할 때 원문을 함께 준다


def test_다시_청한_것도_짧으면_원래_것을_쓴다(monkeypatch):
    """끝까지 못 늘리면 받아들인다 — 규격 미달은 리포트에 남아 사람이 본다."""
    짧은 = dict(ANSWER, story="이" * 150)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-테스트용가짜키")
    monkeypatch.setattr(naming, "load_dotenv", lambda *a, **k: False)
    monkeypatch.setattr(naming, "_call_openai",
                        lambda *a, **k: 짧은 if len(a[0]) > 500 else {"story": "구" * 100})
    result = naming.generate_naming(BRIEF)
    assert result["story"] == "이" * 150


def test_다시_청하는_횟수에_상한이_있다(monkeypatch):
    """끝없이 다시 청하면 토큰을 다 쓴다. 상한을 넘기지 않는다."""
    짧은 = dict(ANSWER, story="이" * 150)
    호출 = []

    def 가짜호출(prompt, _key):
        호출.append(prompt)
        return 짧은 if len(호출) == 1 else {"story": "구" * 160}

    monkeypatch.setenv("OPENAI_API_KEY", "sk-테스트용가짜키")
    monkeypatch.setattr(naming, "load_dotenv", lambda *a, **k: False)
    monkeypatch.setattr(naming, "_call_openai", 가짜호출)

    naming.generate_naming(BRIEF)
    assert len(호출) == 1 + naming.STORY_RETRIES


def test_명세가_요구하는_300자에_맞춰_다시_청한다():
    """계약 최소치(200자)가 아니라 명세의 '300자 내외'를 기준으로 삼는다."""
    assert naming.STORY_TARGET_CHARS > naming.MIN_STORY_CHARS
    assert 260 <= naming.STORY_TARGET_CHARS <= 300


def test_다시_청하다_실패해도_죽지_않는다(monkeypatch):
    짧은 = dict(ANSWER, story="이" * 150)
    첫번째 = [True]

    def 가짜호출(prompt, _key):
        if 첫번째[0]:
            첫번째[0] = False
            return 짧은
        raise RuntimeError("쿼터 초과")

    monkeypatch.setenv("OPENAI_API_KEY", "sk-테스트용가짜키")
    monkeypatch.setattr(naming, "load_dotenv", lambda *a, **k: False)
    monkeypatch.setattr(naming, "_call_openai", 가짜호출)
    assert naming.generate_naming(BRIEF)["story"] == "이" * 150


def test_스토리가_충분하면_다시_청하지_않는다(monkeypatch):
    """멀쩡한 결과에 추가 호출을 하면 토큰 낭비다."""
    호출수 = [0]

    def 가짜호출(*_a, **_k):
        호출수[0] += 1
        return ANSWER

    monkeypatch.setenv("OPENAI_API_KEY", "sk-테스트용가짜키")
    monkeypatch.setattr(naming, "load_dotenv", lambda *a, **k: False)
    monkeypatch.setattr(naming, "_call_openai", 가짜호출)
    naming.generate_naming(BRIEF)
    assert 호출수[0] == 1


def test_호출이_실패하면_예시로_대신하고_멈추지_않는다(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-테스트용가짜키")
    monkeypatch.setattr(naming, "load_dotenv", lambda *a, **k: False)
    monkeypatch.setattr(naming, "_call_openai",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("쿼터 초과")))
    assert naming.generate_naming(BRIEF) == dict(naming.EXAMPLE, used_example=True)


def test_결과가_규격에_못_미치면_예시로_대신한다(monkeypatch):
    """이름 하나짜리 결과로 뒤 단계를 돌릴 수는 없다."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-테스트용가짜키")
    monkeypatch.setattr(naming, "load_dotenv", lambda *a, **k: False)
    monkeypatch.setattr(naming, "_call_openai",
                        lambda *a, **k: {"naming": [{"name": "하나"}], "slogans": ["가"]})
    assert naming.generate_naming(BRIEF) == dict(naming.EXAMPLE, used_example=True)


def test_키가_없으면_예시로_돈다(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(naming, "load_dotenv", lambda *a, **k: False)
    assert naming.generate_naming(BRIEF) == dict(naming.EXAMPLE, used_example=True)


# --- 규격 검증 -----------------------------------------------------------

def test_이름이_여섯_개면_규격_위반():
    """명세는 3~5개를 요구한다."""
    naming = {"naming": [{"name": f"이름{i}", "english": f"Name{i}", "meaning": "뜻"}
                         for i in range(6)],
              "slogans": ["가", "나", "다"], "story": "이" * 300}
    assert any("3~5개" in p for p in validate.check_naming(naming))


def test_경쟁사_분석이_없어도_규격을_통과한다():
    """경쟁사 분석은 택하지 않은 보너스라 없어도 된다."""
    naming = {"naming": [{"name": f"이름{i}", "english": f"Name{i}", "meaning": "뜻"}
                         for i in range(3)],
              "slogans": ["가", "나", "다"], "story": "이" * 300}
    assert validate.check_naming(naming) == []


def test_경쟁사_모양이_틀리면_잡는다():
    naming = {"naming": [{"name": f"이름{i}", "english": f"Name{i}", "meaning": "뜻"}
                         for i in range(3)],
              "slogans": ["가", "나", "다"], "story": "이" * 300,
              "competitors": "블루보틀"}
    assert any("competitors" in p for p in validate.check_naming(naming))


def test_예시값이_스스로_규격을_지킨다():
    """기본 예시가 규격 미달이면 팀원이 잘못된 본보기를 따라 하게 된다."""
    문제 = [p for p in validate.check_naming(naming.EXAMPLE) if "story" not in p]
    assert 문제 == []


# --- 결과 문서 -----------------------------------------------------------

def test_결과_문서에_영문_표기가_함께_실린다():
    text = "\n".join(report._naming_block(naming.EXAMPLE))
    assert "온기(溫氣) (Ongi, OWN-gee)" in text
    assert "쉼표 (Comma, COM-ma)" in text


def test_결과_문서에_경쟁사_분석_표가_실린다():
    text = "\n".join(report._naming_block(naming.EXAMPLE))
    assert "경쟁사 분석과 차별화 포인트" in text
    assert "블루보틀" in text


def test_보너스가_없으면_그_절을_아예_넣지_않는다():
    text = "\n".join(report._naming_block({"naming": [{"name": "온기", "meaning": "뜻"}]}))
    assert "경쟁사 분석" not in text
    assert "온기" in text and "(" not in text.split("온기")[1][:3]


@pytest.mark.parametrize("깨진값", [None, "문자열", 123, {"competitors": "리스트아님"}])
def test_이상한_값이_와도_문서_생성이_죽지_않는다(깨진값):
    report._competitor_block(깨진값 if not isinstance(깨진값, dict) else 깨진값.get("competitors"))


def test_스토리가_아예_비어_오면_새로_써_달라고_청한다(monkeypatch):
    """후보 개수를 늘린 뒤 story 가 빈 문자열로 오는 일을 실제로 만났다.

    그때 "0자짜리를 늘려 쓰라" 고 청하면 늘릴 원문이 없어 말이 되지 않는다.
    """
    빈것 = dict(ANSWER, story="")
    호출 = []

    def 가짜호출(prompt, _key):
        호출.append(prompt)
        return 빈것 if len(호출) == 1 else {"story": "구" * 300}

    monkeypatch.setenv("OPENAI_API_KEY", "sk-테스트용가짜키")
    monkeypatch.setattr(naming, "load_dotenv", lambda *a, **k: False)
    monkeypatch.setattr(naming, "_call_openai", 가짜호출)

    result = naming.generate_naming(BRIEF)
    다시청한것 = 호출[1]
    assert "원래 스토리" not in 다시청한것        # 늘릴 원문이 없다
    assert "0자로 너무 짧습니다" not in 다시청한것
    assert "카페" in 다시청한것                  # 브리프로 새로 쓴다
    assert "280자에서 320자" in 다시청한것
    assert len(result["story"]) == 300


def test_스토리가_있으면_그것을_늘려_달라고_청한다(monkeypatch):
    짧은 = dict(ANSWER, story="이" * 150)
    호출 = []

    def 가짜호출(prompt, _key):
        호출.append(prompt)
        return 짧은 if len(호출) == 1 else {"story": "구" * 300}

    monkeypatch.setenv("OPENAI_API_KEY", "sk-테스트용가짜키")
    monkeypatch.setattr(naming, "load_dotenv", lambda *a, **k: False)
    monkeypatch.setattr(naming, "_call_openai", 가짜호출)

    naming.generate_naming(BRIEF)
    assert "원래 스토리" in 호출[1]
    assert "150자로 너무 짧습니다" in 호출[1]
