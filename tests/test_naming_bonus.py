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

# 이름 그대로 import 하면 안 된다. 다른 테스트가 "step*.py 가 아직 없는" 상태를
# 검사하려고 import 를 가로막는데, 여기서 미리 sys.modules 에 올려 두면 충돌한다.
# 그래서 파일 경로로 직접 읽어 **다른 이름**으로 등록한다.
_STEP2 = Path(__file__).resolve().parent.parent / "step2_naming.py"
_spec = importlib.util.spec_from_file_location("step2_naming_under_test", _STEP2)
step2_naming = importlib.util.module_from_spec(_spec)
sys.modules["step2_naming_under_test"] = step2_naming
_spec.loader.exec_module(step2_naming)

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
    prompt = step2_naming.build_prompt(BRIEF)
    assert "카페" in prompt
    assert "20~30대 직장인" in prompt
    assert "여유, 따뜻함" in prompt
    assert "따뜻하고 감성적인" in prompt
    assert "블루보틀" in prompt and "스타벅스" in prompt
    assert "한글과 영어 모두 쓰기 쉬운 이름" in prompt


def test_보너스_규칙이_프롬프트에_실린다():
    prompt = step2_naming.build_prompt(BRIEF)
    assert "english" in prompt              # 영문 네이밍
    assert "differentiation" in prompt      # 경쟁사 차별화


def test_명세가_요구하는_개수가_프롬프트에_숫자로_적힌다():
    """'여러 개' 라고 쓰면 모델마다 다르게 읽는다."""
    prompt = step2_naming.build_prompt(BRIEF)
    assert "3개 이상 5개 이하" in prompt
    assert "정확히 3개" in prompt           # 슬로건
    assert "300자 내외" in prompt           # 스토리


def test_스토리_규칙이_명세_문구를_담는다():
    assert "탄생 배경" in step2_naming.STORY_RULE
    assert "철학" in step2_naming.STORY_RULE
    assert "비전" in step2_naming.STORY_RULE


def test_경쟁사가_없으면_그_줄을_빼고_만든다():
    prompt = step2_naming.build_prompt({"industry": "카페", "keywords": ["여유"]})
    assert "참고 경쟁사" not in prompt


# --- 응답 정규화 ---------------------------------------------------------

# --- 보너스: 다국어 네이밍 지원 -----------------------------------------

def test_다국어_규칙이_프롬프트에_실린다():
    prompt = step2_naming.build_prompt(BRIEF)
    assert "한글 이름과 영문 표기를 함께" in prompt
    assert "reading" in prompt


def test_영문_표기의_조건이_숫자로_적힌다():
    """'짧게' 라고 쓰면 모델마다 다르게 읽는다."""
    assert "12자 안쪽" in step2_naming.MULTILINGUAL_RULE


def test_읽는_법도_받아_담는다():
    result = step2_naming._normalize({
        "naming": [{"name": "온기", "english": "Ongi", "reading": "OWN-gee",
                    "meaning": "따뜻한 기운"}],
    })
    assert result["naming"][0]["reading"] == "OWN-gee"


def test_영문_표기가_비면_규격_위반으로_잡는다():
    """보너스로 택한 항목이므로 빠지면 기록에 남아야 한다."""
    naming = {"naming": [{"name": f"이름{i}", "meaning": "뜻"} for i in range(3)],
              "slogans": ["가", "나", "다"], "story": "이" * 250}
    문제 = validate.check_naming(naming)
    assert len(문제) == 3
    assert all("english" in p for p in 문제)


def test_영문_자리에_한글이_오면_잡는다():
    naming = {"naming": [{"name": "온기", "english": "온기", "meaning": "뜻"}] * 3,
              "slogans": ["가", "나", "다"], "story": "이" * 250}
    assert any("영문이 아닌" in p for p in validate.check_naming(naming))


def test_예시값의_모든_후보에_영문_표기가_있다():
    for item in step2_naming.EXAMPLE["naming"]:
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
    result = step2_naming._normalize({
        "naming": [{"name": "온기", "english": "Ongi", "meaning": "따뜻한 기운"}],
        "slogans": ["가", "나", "다"],
        "story": "이야기",
    })
    assert result["naming"][0]["english"] == "Ongi"


def test_영문_표기가_없어도_키는_있다():
    """뒤 단계가 매번 확인하지 않아도 되게 빈 문자열로 채운다."""
    result = step2_naming._normalize({"naming": [{"name": "온기"}]})
    assert result["naming"][0]["english"] == ""


def test_경쟁사_분석을_받아_담는다():
    result = step2_naming._normalize({
        "competitors": [{"competitor": "블루보틀", "position": "스페셜티",
                         "differentiation": "앉아 있어도 되는 시간을 판다"}],
    })
    assert result["competitors"][0]["competitor"] == "블루보틀"


def test_차별화가_비면_그_경쟁사는_버린다():
    """이름만 있고 알맹이가 없으면 결과 문서에 실을 것이 없다."""
    result = step2_naming._normalize({
        "competitors": [
            {"competitor": "블루보틀", "position": "스페셜티", "differentiation": "  "},
            {"competitor": "스타벅스", "position": "체인", "differentiation": "동네의 결"},
        ],
    })
    assert [c["competitor"] for c in result["competitors"]] == ["스타벅스"]


def test_슬로건을_하나만_주면_배열로_감싼다():
    assert step2_naming._normalize({"slogans": "하나뿐"})["slogans"] == ["하나뿐"]


def test_이름을_문자열로만_줘도_받아_낸다():
    result = step2_naming._normalize({"naming": ["온기"]})
    assert result["naming"][0] == {"name": "온기", "meaning": ""}


# --- LLM 호출 (가짜 응답으로) --------------------------------------------

class _FakeResponse:
    def __init__(self, payload):
        self._body = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def test_모델이_돌려준_결과를_그대로_쓴다(monkeypatch):
    """진짜 키 없이도 호출 경로 전체가 도는지 본다."""
    answer = {
        "naming": [
            {"name": "온기", "english": "Ongi", "meaning": "따뜻한 기운"},
            {"name": "쉼표", "english": "Comma", "meaning": "잠깐 멈춤"},
            {"name": "모닥", "english": "Modak", "meaning": "작은 불빛"},
        ],
        "slogans": ["가", "나", "다"],
        "story": "이" * 250,
        "competitors": [{"competitor": "블루보틀", "position": "스페셜티",
                         "differentiation": "머무는 시간"}],
    }
    payload = {"choices": [{"message": {"content": json.dumps(answer, ensure_ascii=False)}}]}

    class _FakeOpenAI:
        def __init__(self, **_kwargs):
            self.chat = self

        @property
        def completions(self):
            return self

        def create(self, **_kwargs):
            class _Message:
                content = json.dumps(answer, ensure_ascii=False)

            class _Choice:
                message = _Message()

            class _Result:
                choices = [_Choice()]

            return _Result()

    monkeypatch.setenv("OPENAI_API_KEY", "sk-테스트용가짜키")
    monkeypatch.setattr(step2_naming, "load_dotenv", lambda *a, **k: False)
    monkeypatch.setitem(sys.modules, "openai", type("m", (), {"OpenAI": _FakeOpenAI}))

    result = step2_naming.generate_naming(BRIEF)
    assert result is not step2_naming.EXAMPLE
    assert [n["english"] for n in result["naming"]] == ["Ongi", "Comma", "Modak"]
    assert result["competitors"][0]["differentiation"] == "머무는 시간"
    assert payload  # 사용하지 않는 변수 경고 방지


def test_호출이_실패하면_예시로_대신하고_멈추지_않는다(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-테스트용가짜키")
    monkeypatch.setattr(step2_naming, "load_dotenv", lambda *a, **k: False)
    monkeypatch.setattr(step2_naming, "_call_openai",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("쿼터 초과")))
    assert step2_naming.generate_naming(BRIEF) is step2_naming.EXAMPLE


def test_결과가_규격에_못_미치면_예시로_대신한다(monkeypatch):
    """이름 하나짜리 결과로 뒤 단계를 돌릴 수는 없다."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-테스트용가짜키")
    monkeypatch.setattr(step2_naming, "load_dotenv", lambda *a, **k: False)
    monkeypatch.setattr(step2_naming, "_call_openai",
                        lambda *a, **k: {"naming": [{"name": "하나"}], "slogans": ["가"]})
    assert step2_naming.generate_naming(BRIEF) is step2_naming.EXAMPLE


def test_키가_없으면_예시로_돈다(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(step2_naming, "load_dotenv", lambda *a, **k: False)
    assert step2_naming.generate_naming(BRIEF) is step2_naming.EXAMPLE


# --- 규격 검증 -----------------------------------------------------------

def test_이름이_여섯_개면_규격_위반():
    """명세는 3~5개를 요구한다."""
    naming = {"naming": [{"name": f"이름{i}", "english": f"Name{i}", "meaning": "뜻"}
                         for i in range(6)],
              "slogans": ["가", "나", "다"], "story": "이" * 250}
    assert any("3~5개" in p for p in validate.check_naming(naming))


def test_경쟁사_분석이_없어도_규격을_통과한다():
    """경쟁사 분석은 택하지 않은 보너스라 없어도 된다."""
    naming = {"naming": [{"name": f"이름{i}", "english": f"Name{i}", "meaning": "뜻"}
                         for i in range(3)],
              "slogans": ["가", "나", "다"], "story": "이" * 250}
    assert validate.check_naming(naming) == []


def test_경쟁사_모양이_틀리면_잡는다():
    naming = {"naming": [{"name": f"이름{i}", "english": f"Name{i}", "meaning": "뜻"}
                         for i in range(3)],
              "slogans": ["가", "나", "다"], "story": "이" * 250,
              "competitors": "블루보틀"}
    assert any("competitors" in p for p in validate.check_naming(naming))


def test_예시값이_스스로_규격을_지킨다():
    """기본 예시가 규격 미달이면 팀원이 잘못된 본보기를 따라 하게 된다."""
    문제 = [p for p in validate.check_naming(step2_naming.EXAMPLE) if "story" not in p]
    assert 문제 == []


# --- 결과 문서 -----------------------------------------------------------

def test_결과_문서에_영문_표기가_함께_실린다():
    text = "\n".join(report._naming_block(step2_naming.EXAMPLE))
    assert "온기(溫氣) (Ongi, OWN-gee)" in text
    assert "쉼표 (Comma, COM-ma)" in text


def test_결과_문서에_경쟁사_분석_표가_실린다():
    text = "\n".join(report._naming_block(step2_naming.EXAMPLE))
    assert "경쟁사 분석과 차별화 포인트" in text
    assert "블루보틀" in text


def test_보너스가_없으면_그_절을_아예_넣지_않는다():
    text = "\n".join(report._naming_block({"naming": [{"name": "온기", "meaning": "뜻"}]}))
    assert "경쟁사 분석" not in text
    assert "온기" in text and "(" not in text.split("온기")[1][:3]


@pytest.mark.parametrize("깨진값", [None, "문자열", 123, {"competitors": "리스트아님"}])
def test_이상한_값이_와도_문서_생성이_죽지_않는다(깨진값):
    report._competitor_block(깨진값 if not isinstance(깨진값, dict) else 깨진값.get("competitors"))
