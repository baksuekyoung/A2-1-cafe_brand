"""컬러 팔레트 PNG 와 로고 프롬프트.

명세가 요구하는 산출물 두 가지를 검증한다.

- "컬러 팔레트를 시각화하여 PNG 이미지로 저장"
- 로고 프롬프트는 **영어여야 한다.** 한국어를 이미지 API 에 넘기면
  로고가 아니라 인물 사진이 나온다.
"""

import importlib.util
import struct
import sys
from pathlib import Path

import pytest

from brand_result import logo_prompt, palette_png

PALETTE = {
    "main": {"hex": "#3E3028", "name": "로스팅 브라운", "reason": "원두를 볶은 색"},
    "subs": [
        {"hex": "#F5F0E8", "name": "크림", "reason": "여백"},
        {"hex": "#7C9070", "name": "세이지", "reason": "포인트"},
    ],
}

BRIEF = {
    "industry": "카페",
    "target": "20~30대 직장인",
    "keywords": ["여유", "따뜻함"],
}

NAMING = {"naming": [{"name": "온기(溫氣)", "meaning": "따뜻한 기운"}]}


def _png_size(data: bytes) -> tuple[int, int]:
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "PNG 시그니처가 아닙니다"
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def test_팔레트_png_가_만들어진다(tmp_path):
    path = palette_png.save_palette_png(PALETTE, tmp_path)
    assert path.name == "color_palette.png"
    width, height = _png_size(path.read_bytes())
    assert width > 100 and height > 100


def test_matplotlib_없이도_만들어진다(tmp_path):
    """[5] 는 외부 패키지 없이 돌아가는 것이 약속이다."""
    path = tmp_path / "color_palette.png"
    palette_png._render_builtin(PALETTE, path)
    width, height = _png_size(path.read_bytes())
    assert width == palette_png.WIDTH


def test_망가진_hex_여도_죽지_않는다(tmp_path):
    """[3] 이 'rgb(1,2,3)' 을 주더라도 저장은 되어야 한다."""
    깨진_팔레트 = {"main": {"hex": "rgb(62,48,40)"}, "subs": [{"hex": "없음"}]}
    path = tmp_path / "color_palette.png"
    palette_png._render_builtin(깨진_팔레트, path)
    _png_size(path.read_bytes())


def test_서브색이_없어도_만들어진다(tmp_path):
    path = tmp_path / "color_palette.png"
    palette_png._render_builtin({"main": {"hex": "#3E3028"}, "subs": []}, path)
    _png_size(path.read_bytes())


def test_밝은_색_위에는_검은_글자():
    assert palette_png._text_color((245, 240, 232)) == (0, 0, 0)
    assert palette_png._text_color((62, 48, 40)) == (255, 255, 255)


# --- 로고 프롬프트 -------------------------------------------------------

def test_프롬프트에_한국어가_들어가지_않는다():
    """이게 이 파일에서 제일 중요한 검사다."""
    for prompt in logo_prompt.build_prompts(BRIEF, NAMING, PALETTE):
        assert all(ord(char) < 128 for char in prompt), f"한국어가 남았습니다: {prompt}"


def test_키워드가_영어로_옮겨진다():
    prompts = logo_prompt.build_prompts(BRIEF, NAMING, PALETTE)
    assert "calm and unhurried ease" in prompts[0]
    assert "warmth" in prompts[1]


def test_색이_영어_이름으로_들어간다():
    assert "roasted coffee brown" in logo_prompt.build_prompts(BRIEF, NAMING, PALETTE)[0]


def test_배경을_흰색으로_못_박는다():
    """빼면 배경이 브랜드 색으로 칠해져 나온다. 실제로 그렇게 나왔다."""
    for prompt in logo_prompt.build_prompts(BRIEF, NAMING, PALETTE):
        assert "pure white background" in prompt


def test_logo_라는_낱말을_쓰지_않는다():
    """모델이 'logo' 를 보면 밑에 뭉개진 가짜 글씨를 같이 그린다."""
    for prompt in logo_prompt.build_prompts(BRIEF, NAMING, PALETTE):
        assert "logo" not in prompt.lower()


def test_글자_금지를_여러_표현으로_반복한다():
    """한 번만 적으면 무료 모델이 흘려버린다."""
    for prompt in logo_prompt.build_prompts(BRIEF, NAMING, PALETTE):
        금지 = [낱말 for 낱말 in ("no lettering", "no words", "no signature", "no watermark",
                                  "wordless", "textless", "no typography", "no letters",
                                  "no numbers") if 낱말 in prompt]
        assert len(금지) >= 3, prompt


def test_브랜드명은_어느_프롬프트에도_넣지_않는다():
    """이름을 넣으면 모델이 그것을 그림 안에 써 넣으려다 글자를 뭉갠다."""
    naming = {"naming": [{"name": "온기", "english": "Ongi", "meaning": "따뜻한 기운"}]}
    for prompt in logo_prompt.build_prompts(BRIEF, naming, PALETTE):
        assert "Ongi" not in prompt
        assert "온기" not in prompt
        assert "called" not in prompt


def test_모르는_키워드는_넣지_않고_기본값을_쓴다():
    """낱말표에 없으면 한국어를 그대로 넣는 대신 뺀다."""
    brief = {"industry": "카페", "keywords": ["아직없는낱말"]}
    prompt = logo_prompt.build_prompts(brief, None, None)[0]
    assert "아직없는낱말" not in prompt
    assert logo_prompt.DEFAULT_THEME in prompt


def test_브리프가_비어도_프롬프트가_나온다():
    prompts = logo_prompt.build_prompts({}, None, None)
    assert len(prompts) == 2
    assert all(prompt.strip() for prompt in prompts)


def test_이미_영어인_값은_그대로_쓴다():
    assert logo_prompt.to_english("bakery") == "bakery"


def test_명세가_요구하는_장수만큼_만든다():
    """로고 시안 2~3개."""
    assert 2 <= len(logo_prompt.build_prompts(BRIEF, NAMING, PALETTE)) <= 3


# --- 사람이 직접 쓸 프롬프트 -------------------------------------------

def test_직접_쓸_프롬프트에는_브랜드_이름이_없다():
    """'logo for a brand called OO' 는 상표 정책에 걸려 거절당한다."""
    for prompt in logo_prompt.build_human_prompts(BRIEF, PALETTE):
        assert "called" not in prompt
        assert "brand" not in prompt.lower()


def test_직접_쓸_프롬프트는_문장으로_되어_있다():
    """쉼표 나열식을 대화형 도구에 넣으면 그림을 안 그리고 되묻는다."""
    for prompt in logo_prompt.build_human_prompts(BRIEF, PALETTE):
        assert prompt.startswith("Draw ")
        assert prompt.rstrip().endswith(".")


def test_직접_쓸_프롬프트에도_한국어가_없다():
    for prompt in logo_prompt.build_human_prompts(BRIEF, PALETTE):
        assert all(ord(char) < 128 for char in prompt), prompt


def test_직접_쓸_프롬프트에_글자_금지가_들어간다():
    """넣지 않으면 로고 안에 깨진 글씨가 같이 나온다."""
    for prompt in logo_prompt.build_human_prompts(BRIEF, PALETTE):
        assert "Do not include any letters" in prompt
        assert "completely wordless" in prompt


def test_직접_쓸_프롬프트도_배경을_흰색으로_못_박는다():
    for prompt in logo_prompt.build_human_prompts(BRIEF, PALETTE):
        assert "pure white background" in prompt


def test_직접_쓸_프롬프트에_색_이름이_들어간다():
    assert "roasted coffee brown" in logo_prompt.build_human_prompts(BRIEF, PALETTE)[0]


def test_문서가_두_가지_프롬프트를_모두_담는다():
    api = logo_prompt.build_prompts(BRIEF, NAMING, PALETTE)
    human = logo_prompt.build_human_prompts(BRIEF, PALETTE)
    text = logo_prompt.build_markdown(api, ["pollinations", "pollinations"], human)
    assert "직접 만드실 때" in text
    for prompt in api + human:
        assert prompt in text


def test_프롬프트_문서에_프롬프트가_그대로_담긴다():
    prompts = logo_prompt.build_prompts(BRIEF, NAMING, PALETTE)
    text = logo_prompt.build_markdown(prompts, ["placeholder", "placeholder"])
    for prompt in prompts:
        assert prompt in text
    assert "자리표시자" in text


def test_키가_없으면_llm_번역을_시도하지_않는다(monkeypatch):
    for key in ("OPENAI_API_KEY", "GEMINI_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    assert logo_prompt.translate_themes_with_llm(BRIEF) is None


def test_키가_있어도_문장_구조는_템플릿이_쥔다(monkeypatch):
    """예전에 프롬프트 전체를 LLM 에게 맡겼더니 흰 배경·글자 금지·색 이름을
    통째로 지우고 자기 문장으로 다시 썼다. 로고가 팔레트와 다른 색으로 나왔다."""
    monkeypatch.setattr(logo_prompt, "translate_themes_with_llm",
                        lambda _brief: ["deep stillness", "gentle heat"])
    prompts = logo_prompt.make_prompts(BRIEF, NAMING, PALETTE)

    assert "deep stillness" in prompts[0]          # 번역은 반영되고
    for prompt in prompts:                         # 규칙은 그대로 남는다
        assert "pure white background" in prompt
        assert "roasted coffee brown" in prompt
        assert "logo" not in prompt.lower()


def test_llm_번역이_실패해도_낱말표로_만든다(monkeypatch):
    monkeypatch.setattr(logo_prompt, "translate_themes_with_llm", lambda _brief: None)
    prompts = logo_prompt.make_prompts(BRIEF, NAMING, PALETTE)
    assert "calm and unhurried ease" in prompts[0]


def test_번역에_한국어가_섞여_오면_버린다(monkeypatch):
    """모델이 한국어를 남기면 이미지 API 가 엉뚱한 그림을 그린다."""
    import json as _json
    monkeypatch.setenv("OPENAI_API_KEY", "sk-테스트")
    monkeypatch.setattr(logo_prompt, "_ask_json",
                        lambda *a, **k: _json.loads('{"themes": ["여유", "warmth"]}'))
    assert logo_prompt.translate_themes_with_llm(BRIEF) == ["warmth"]


# --- 로고 개수 (명세: 2~3장) -----------------------------------------------

def test_시안을_세_장까지_만들_수_있다():
    """명세는 2~3장이다. 템플릿이 두 개뿐이면 3장을 요청해도 2장만 나온다."""
    assert len(logo_prompt.PROMPT_TEMPLATES) >= 3
    assert len(logo_prompt.build_prompts(BRIEF, NAMING, PALETTE, count=3)) == 3


def test_시안마다_다른_템플릿을_쓴다():
    """같은 그림이 두 장 나오면 '시안' 이 아니다."""
    prompts = logo_prompt.build_prompts(BRIEF, NAMING, PALETTE, count=3)
    assert len(set(prompts)) == 3


def test_세_번째_템플릿도_글자를_금지한다():
    """새로 넣은 템플릿이 규칙을 빠뜨리면 거기서만 글자가 나온다."""
    for template in logo_prompt.PROMPT_TEMPLATES:
        낮춘것 = template.lower()
        assert "logo" not in 낮춘것
        assert "pure white background" in 낮춘것
        assert 낮춘것.count("no ") >= 3        # 한 번만 적으면 흘려버린다


def test_사람용_문장도_시안_수만큼_있다():
    assert len(logo_prompt.HUMAN_CONCEPTS) >= 3
    assert len(logo_prompt.build_human_prompts(BRIEF, PALETTE, 3)) == 3


# `import logo` 로 올리면 안 된다. 다른 테스트가 "단계 파일이 아직 없는" 상태를
# 검사하려고 import 를 가로막는데, 여기서 sys.modules 에 올려 두면 그게 깨진다.
# 그래서 파일 경로로 직접 읽어 다른 이름으로 등록한다.
_LOGO_PATH = Path(__file__).resolve().parent.parent / "logo.py"
_logo_spec = importlib.util.spec_from_file_location("logo_under_test", _LOGO_PATH)
logo_module = importlib.util.module_from_spec(_logo_spec)
sys.modules["logo_under_test"] = logo_module
_logo_spec.loader.exec_module(logo_module)


def test_환경변수로_로고_수를_올린다(monkeypatch):
    """`main.py --logos 3` 이 이 환경변수를 세운다."""
    for 값, 기대 in (("3", 3), ("2", 2), ("1", 2), ("9", 3), ("", 2), ("셋", 2)):
        monkeypatch.setenv("LOGO_COUNT", 값)
        assert logo_module._logo_count() == 기대, f"LOGO_COUNT={값!r}"


def test_환경변수가_없으면_두_장이다(monkeypatch):
    monkeypatch.delenv("LOGO_COUNT", raising=False)
    assert logo_module._logo_count() == logo_module.LOGO_COUNT == 2
