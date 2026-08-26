"""코디세이 공개 API 연동.

실제 호출은 하지 않는다. `urlopen` 을 가짜로 바꿔 보내는 요청과 읽는 응답만 본다.

실측으로 확인한 것 (2026-08-26):
  - 채팅은 OpenAI 규격이지만 `response_format` 을 받지 않는다 (HTTP 400)
  - 이미지 응답 경로가 OpenAI 와 다르다 — result.images[0].b64_json
  - '클로드' 라벨 키는 채팅에서 403, 이미지만 된다
"""

import base64
import importlib.util
import io
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

_ROOT = Path(__file__).resolve().parent.parent


def _모듈(파일명, 별명):
    """단계 파일을 다른 이름으로 올린다 (다른 테스트의 import 차단과 안 부딪히게)."""
    spec = importlib.util.spec_from_file_location(별명, _ROOT / 파일명)
    module = importlib.util.module_from_spec(spec)
    sys.modules[별명] = module
    spec.loader.exec_module(module)
    return module


naming = _모듈("naming.py", "naming_codyssey_test")
logo = _모듈("logo.py", "logo_codyssey_test")

PNG = bytes.fromhex("89504e470d0a1a0a") + b"rest-of-png"


class 가짜응답(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


def _가짜urlopen(monkeypatch, 모듈, 답, 보낸것):
    def urlopen(request, timeout=None):
        보낸것.append({
            "url": request.full_url,
            "body": json.loads(request.data.decode("utf-8")),
            "headers": dict(request.headers),
        })
        본문 = 답(보낸것[-1]) if callable(답) else 답
        return 가짜응답(json.dumps(본문).encode("utf-8"))

    monkeypatch.setattr(모듈.urllib.request, "urlopen", urlopen)


# --- 채팅 -------------------------------------------------------------------

def test_코디세이는_response_format_을_보내지_않는다(monkeypatch):
    """보내면 HTTP 400 unsupported_feature 가 온다 (실측)."""
    보낸것 = []
    _가짜urlopen(monkeypatch, naming,
                {"choices": [{"message": {"content": '{"naming": []}'}}]}, 보낸것)

    naming._call_codyssey("프롬프트", "sk-cody-테스트")
    assert "response_format" not in 보낸것[0]["body"]


def test_openai_는_response_format_을_보낸다(monkeypatch):
    """이쪽은 지원하므로 계속 쓴다 — JSON 이 깨질 확률이 낮아진다."""
    보낸것 = []
    _가짜urlopen(monkeypatch, naming,
                {"choices": [{"message": {"content": '{"naming": []}'}}]}, 보낸것)

    naming._call_openai("프롬프트", "sk-테스트")
    assert 보낸것[0]["body"]["response_format"] == {"type": "json_object"}


def test_코디세이_주소로_보낸다(monkeypatch):
    보낸것 = []
    _가짜urlopen(monkeypatch, naming,
                {"choices": [{"message": {"content": "{}"}}]}, 보낸것)

    naming._call_codyssey("프롬프트", "sk-cody-테스트")
    assert 보낸것[0]["url"] == "https://copa.codyssey.kr/v1/chat/completions"
    assert 보낸것[0]["headers"]["Authorization"] == "Bearer sk-cody-테스트"


def test_주소를_환경변수로_바꿀_수_있다(monkeypatch):
    """공지가 'Base URL 은 환경(QA/운영)마다 다르다' 고 했다."""
    monkeypatch.setenv("CODYSSEY_BASE_URL", "https://qa.example.kr/")
    보낸것 = []
    _가짜urlopen(monkeypatch, naming,
                {"choices": [{"message": {"content": "{}"}}]}, 보낸것)

    naming._call_codyssey("프롬프트", "키")
    assert 보낸것[0]["url"] == "https://qa.example.kr/v1/chat/completions"


def test_코드블록_울타리를_벗긴다(monkeypatch):
    """JSON 강제 모드를 못 쓰므로 ```json 으로 감싸 오는 일이 있다."""
    보낸것 = []
    _가짜urlopen(monkeypatch, naming,
                {"choices": [{"message": {"content": '```json\n{"story": "가"}\n```'}}]},
                보낸것)

    assert naming._call_codyssey("프롬프트", "키") == {"story": "가"}


def test_울타리가_없어도_그대로_읽는다():
    assert naming._strip_fence('{"a": 1}') == '{"a": 1}'
    assert naming._strip_fence('```\n{"a": 1}\n```') == '{"a": 1}'
    assert naming._strip_fence('```json\n{"a": 1}\n```') == '{"a": 1}'


def test_모델을_앞에서부터_시도한다(monkeypatch):
    """앞 모델이 막히면 다음으로 넘어간다."""
    보낸것 = []

    def 답(요청):
        if 요청["body"]["model"] == naming.CODYSSEY_MODELS[0]:
            raise RuntimeError("막힘")
        return {"choices": [{"message": {"content": "{}"}}]}

    _가짜urlopen(monkeypatch, naming, 답, 보낸것)
    naming._call_codyssey("프롬프트", "키")
    assert [b["body"]["model"] for b in 보낸것][:2] == list(naming.CODYSSEY_MODELS[:2])


def test_전부_막히면_예외를_던진다(monkeypatch):
    def 답(_요청):
        raise RuntimeError("막힘")

    _가짜urlopen(monkeypatch, naming, 답, [])
    with pytest.raises(RuntimeError, match="코디세이"):
        naming._call_codyssey("프롬프트", "키")


# --- 공급자 순서 ------------------------------------------------------------

def test_코디세이가_맨_앞이다(monkeypatch):
    """기관 키로 정산되므로 개인 결제분보다 먼저 쓴다."""
    monkeypatch.setenv("CODYSSEY_OPENAI_KEY", "sk-cody")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-개인")
    monkeypatch.setenv("GEMINI_API_KEY", "AQ.개인")
    이름, 키, 호출 = naming._pick_provider()
    assert (이름, 키, 호출) == ("코디세이", "sk-cody", naming._call_codyssey)


def test_코디세이가_없으면_openai_로_이어진다(monkeypatch):
    monkeypatch.delenv("CODYSSEY_OPENAI_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-개인")
    assert naming._pick_provider()[0] == "OpenAI"


def test_키가_하나도_없으면_빈_키를_돌려준다(monkeypatch):
    for 이름 in ("CODYSSEY_OPENAI_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY"):
        monkeypatch.delenv(이름, raising=False)
    assert naming._pick_provider()[1] == ""


# --- 이미지 -----------------------------------------------------------------

def test_이미지_응답_경로가_openai_와_다르다(monkeypatch):
    """OpenAI 는 data[0], 코디세이는 result.images[0] 이다."""
    보낸것 = []
    _가짜urlopen(monkeypatch, logo, {
        "result": {"images": [{"b64_json": base64.b64encode(PNG).decode()}]}
    }, 보낸것)

    assert logo._codyssey_image("프롬프트", "sk-cody") == PNG
    assert 보낸것[0]["url"] == "https://copa.codyssey.kr/api/v1/images"


def test_이미지는_b64_json_을_요구한다(monkeypatch):
    """안 주면 서버 url 만 오고 키만으로는 못 받는다 (문서 주석)."""
    보낸것 = []
    _가짜urlopen(monkeypatch, logo, {
        "result": {"images": [{"b64_json": base64.b64encode(PNG).decode()}]}
    }, 보낸것)

    logo._codyssey_image("프롬프트", "키")
    assert 보낸것[0]["body"]["response_format"] == "b64_json"
    assert 보낸것[0]["body"]["size"] == "1024x1024"


def test_이미지_모델을_앞에서부터_시도한다(monkeypatch):
    보낸것 = []

    def 답(요청):
        if 요청["body"]["model"] == logo.CODYSSEY_IMAGE_MODELS[0]:
            raise RuntimeError("막힘")
        return {"result": {"images": [{"b64_json": base64.b64encode(PNG).decode()}]}}

    _가짜urlopen(monkeypatch, logo, 답, 보낸것)
    assert logo._codyssey_image("프롬프트", "키") == PNG
    assert 보낸것[1]["body"]["model"] == logo.CODYSSEY_IMAGE_MODELS[1]


def test_이미지가_전부_막히면_None(monkeypatch):
    def 답(_요청):
        raise RuntimeError("막힘")

    _가짜urlopen(monkeypatch, logo, 답, [])
    assert logo._codyssey_image("프롬프트", "키") is None


def test_로고가_코디세이를_먼저_쓴다(monkeypatch):
    """공급자 순서: 코디세이 → OpenAI → Pollinations."""
    monkeypatch.setenv("CODYSSEY_OPENAI_KEY", "sk-cody")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-개인")
    monkeypatch.setattr(logo, "load_dotenv", lambda *a, **k: False)
    monkeypatch.setattr(logo, "_codyssey_image", lambda *a, **k: PNG)
    monkeypatch.setattr(logo, "_openai_image",
                        lambda *a, **k: pytest.fail("개인 키를 먼저 썼습니다"))

    결과 = logo.generate_logos({"industry": "카페"})
    assert [item["source"] for item in 결과] == ["codyssey"] * len(결과)


def test_코디세이가_실패하면_openai_로_이어진다(monkeypatch):
    monkeypatch.setenv("CODYSSEY_OPENAI_KEY", "sk-cody")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-개인")
    monkeypatch.setattr(logo, "load_dotenv", lambda *a, **k: False)
    monkeypatch.setattr(logo, "_codyssey_image", lambda *a, **k: None)
    monkeypatch.setattr(logo, "_openai_image", lambda *a, **k: PNG)

    결과 = logo.generate_logos({"industry": "카페"})
    assert [item["source"] for item in 결과] == ["openai"] * len(결과)
