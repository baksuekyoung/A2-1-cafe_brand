"""컬러 팔레트 PNG 와 로고 프롬프트.

명세가 요구하는 산출물 두 가지를 검증한다.

- "컬러 팔레트를 시각화하여 PNG 이미지로 저장"
- 로고 프롬프트는 **영어여야 한다.** 한국어를 이미지 API 에 넘기면
  로고가 아니라 인물 사진이 나온다.
"""

import struct

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


def test_업종과_색이_영어로_들어간다():
    prompt = logo_prompt.build_prompts(BRIEF, NAMING, PALETTE)[0]
    assert "cafe" in prompt
    assert "roasted coffee brown" in prompt


def test_한글_브랜드명은_아예_빼고_만든다():
    """'온기(溫氣)' 를 넘기면 모델이 한자를 그리려 든다."""
    prompt = logo_prompt.build_prompts(BRIEF, NAMING, PALETTE)[0]
    assert "온기" not in prompt and "called" not in prompt


def test_영문_이름이_있으면_넣는다():
    naming = {"naming": [{"name": "온기", "english": "Ongi", "meaning": "따뜻한 기운"}]}
    assert "called Ongi" in logo_prompt.build_prompts(BRIEF, naming, PALETTE)[0]


def test_모르는_키워드는_넣지_않고_기본값을_쓴다():
    """낱말표에 없으면 한국어를 그대로 넣는 대신 뺀다."""
    brief = {"industry": "카페", "keywords": ["아직없는낱말"]}
    prompt = logo_prompt.build_prompts(brief, None, None)[0]
    assert "아직없는낱말" not in prompt
    assert logo_prompt.DEFAULT_THEME in prompt


def test_브리프가_비어도_프롬프트가_나온다():
    prompts = logo_prompt.build_prompts({}, None, None)
    assert len(prompts) == 2
    assert all(prompt.startswith(logo_prompt.STYLE) for prompt in prompts)


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


@pytest.mark.parametrize("key", ["OPENAI_API_KEY"])
def test_키가_없으면_llm_번역을_시도하지_않는다(monkeypatch, key):
    monkeypatch.delenv(key, raising=False)
    assert logo_prompt.translate_with_llm(BRIEF, NAMING, PALETTE) is None
