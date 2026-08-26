"""[4] 로고 시안

이미지 생성 API 로 로고 시안을 2~3장 만들어 PNG 바이트로 돌려준다.

## 동작

    OPENAI_API_KEY 가 있으면   →  OpenAI 이미지 생성 API (gpt-image-1 → dall-e-3)
    GEMINI_API_KEY 가 있으면   →  Gemini 이미지 생성 API
    둘 다 없거나 실패하면      →  Pollinations (키 없이 쓸 수 있는 무료 API)
    그것도 실패하면            →  자리표시자 PNG (파이프라인은 중단하지 않는다)

세 번째가 중요하다. 발표 당일 키가 막히거나 인터넷이 끊겨도 전체 실행이
멈추지 않는다. 무엇을 썼는지는 `run_report.md` 와 결과 문서에 남는다.

## 프롬프트를 영어로 쓰는 이유

한국어 브리프를 이미지 API 에 그대로 넘기면 엉뚱한 그림이 나온다.
"20-30대 직장인" 을 인물 사진 요청으로 읽어 로고 자리에 사람 얼굴이 나온 적이 있다.
그래서 브리프의 한국어를 영어 장면 묘사로 옮겨 넣고, 쓴 프롬프트를 그대로
`prompt` 에 담아 결과 문서에 근거로 남긴다.

색은 HEX 대신 **색 이름**을 넣는다. 이미지 모델은 `#3E3028` 을 거의 무시하고
`roasting brown` 은 알아듣는다.
"""

from __future__ import annotations

import base64
import json
import os
import urllib.parse
import urllib.error
import urllib.request
from pathlib import Path

sys_path = str(Path(__file__).resolve().parent)
if sys_path not in __import__("sys").path:
    __import__("sys").path.insert(0, sys_path)

from brand_result import logo_prompt

ENV_PATH = Path(__file__).resolve().parent / ".env"

try:
    from dotenv import load_dotenv
except ImportError:  # python-dotenv 를 안 깔았어도 돌아가야 한다
    def load_dotenv(*_args, **_kwargs) -> bool:
        return False

# 1x1 투명 PNG. 모든 경로가 막혔을 때 자리만 채운다.
PLACEHOLDER = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)

OPENAI_IMAGE_URL = "https://api.openai.com/v1/images/generations"
GEMINI_IMAGE_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)
GEMINI_IMAGE_MODELS = ("gemini-2.5-flash-image", "gemini-3.1-flash-image",
                       "gemini-3-pro-image")
POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}"

# 계정마다 열려 있는 모델이 다르다. 앞에서부터 시도해 먼저 되는 것을 쓴다.
OPENAI_MODELS = ("gpt-image-1", "dall-e-3")

# 명세는 2~3장을 요구한다. 기본 2장, 환경변수로 3장까지.
LOGO_COUNT = logo_prompt.LOGO_COUNT
MAX_LOGO_COUNT = logo_prompt.MAX_LOGO_COUNT


def _logo_count() -> int:
    """만들 시안 수. `LOGO_COUNT` 환경변수로 조절한다 (2~3).

    `main.py --logos 3` 이 이 환경변수를 세운다. 계약이 정한
    `generate_logos(brief, naming, palette)` 서명을 건드리지 않으려는 것이다.
    """
    raw = (os.environ.get("LOGO_COUNT") or "").strip()
    if not raw.isdigit():
        return LOGO_COUNT
    return max(LOGO_COUNT, min(int(raw), MAX_LOGO_COUNT))

# 파이썬 기본 User-Agent 는 Pollinations 앞단 방화벽이 403 으로 막는다.
BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
TIMEOUT = 90


def _openai_image(prompt: str, api_key: str) -> bytes | None:
    """OpenAI 이미지 생성 API 를 부른다. 못 쓰면 None."""
    for model in OPENAI_MODELS:
        body = json.dumps({
            "model": model,
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024",
        }).encode("utf-8")
        request = urllib.request.Request(
            OPENAI_IMAGE_URL,
            data=body,
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {api_key}"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                payload = json.loads(response.read().decode("utf-8"))
            item = (payload.get("data") or [{}])[0]
            if item.get("b64_json"):
                return _to_png(base64.b64decode(item["b64_json"]))
            if item.get("url"):
                with urllib.request.urlopen(item["url"], timeout=TIMEOUT) as image:
                    return _to_png(image.read())
        except urllib.error.HTTPError as exc:
            # 401·403 은 모델 문제가 아니라 키 문제다. 조용히 무료 API 로 넘어가면
            # 사용자는 자기 키가 틀린 줄 모른 채 엉뚱한 결과를 받는다.
            if exc.code in (401, 403):
                print(f"   ⚠️  [4] OpenAI 키가 거부되었습니다 (HTTP {exc.code})"
                      " — .env 의 OPENAI_API_KEY 와 결제 상태를 확인하세요")
                return None
            continue  # 이 모델은 못 쓴다. 다음 후보로.
        except Exception:
            continue
    return None


def _gemini_image(prompt: str, api_key: str) -> bytes | None:
    """Gemini 이미지 생성 API 를 부른다. 못 쓰면 None.

    응답을 읽는 데까지 try 안에 둔다. 안전 필터에 걸려 이미지가 안 실려 와도
    다음 모델로 넘어가야 하기 때문이다.
    """
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
    for model in GEMINI_IMAGE_MODELS:
        request = urllib.request.Request(
            GEMINI_IMAGE_URL.format(model=model),
            data=body,
            headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                payload = json.loads(response.read().decode("utf-8"))
            parts = (payload["candidates"][0].get("content") or {}).get("parts") or []
            for part in parts:
                inline = part.get("inlineData") or part.get("inline_data")
                if inline and inline.get("data"):
                    return _to_png(base64.b64decode(inline["data"]))
        except Exception:
            continue  # 이 모델은 못 쓴다. 다음 후보로.
    return None


def _to_png(data: bytes) -> bytes | None:
    """받은 이미지를 PNG 로 만든다. 명세가 PNG 를 요구한다.

    Pollinations 는 JPEG 로 돌려준다. Pillow 가 있으면 변환하고, 없으면 포기한다 —
    JPEG 를 `.png` 이름으로 저장하면 파일이 깨진 것과 같다.
    """
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return data
    if data[:2] != b"\xff\xd8":
        return None  # 이미지가 아니다. 오류 페이지를 받은 것이다.

    try:
        import io

        from PIL import Image
    except ImportError:
        return None

    try:
        buffer = io.BytesIO()
        Image.open(io.BytesIO(data)).convert("RGB").save(buffer, format="PNG")
        return buffer.getvalue()
    except Exception:
        return None


def _pollinations_image(prompt: str) -> bytes | None:
    """키 없이 쓸 수 있는 무료 이미지 API. 마지막 보루다.

    User-Agent 를 반드시 보낸다. 파이썬 기본 UA 로 부르면 앞단 방화벽이
    HTTP 403 으로 막는다 (봇으로 본다).
    """
    # model=flux 를 지정한다. 기본 모델은 "no text" 를 흘려버리고 로고 아래
    # 뭉개진 가짜 글씨를 같이 그린다. flux 는 그 지시를 지킨다.
    url = (POLLINATIONS_URL.format(prompt=urllib.parse.quote(prompt))
           + "?width=1024&height=1024&nologo=true&model=flux")
    request = urllib.request.Request(url, headers={"User-Agent": BROWSER_UA})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            data = response.read()
    except Exception:
        return None
    return _to_png(data)


def generate_logos(brief: dict, naming: dict | None = None,
                   palette: dict | None = None) -> list:
    """docs/데이터-계약.md 의 [4] 규격대로 list 를 돌려준다."""
    # 경로를 직접 준다 — 인자 없이 부르면 다른 폴더에서 실행했을 때 못 찾는다.
    try:
        load_dotenv(ENV_PATH)
    except Exception:
        pass

    openai_key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    gemini_key = (os.environ.get("GEMINI_API_KEY") or "").strip()

    logos = []
    for prompt in logo_prompt.make_prompts(brief or {}, naming, palette, _logo_count()):
        image, source = None, ""
        if openai_key:
            image, source = _openai_image(prompt, openai_key), "openai"
        if image is None and gemini_key:
            image, source = _gemini_image(prompt, gemini_key), "gemini"
        if image is None:
            image = _pollinations_image(prompt)
            source = "pollinations"
        if image is None:
            image = PLACEHOLDER
            source = "placeholder"
            print(f"   ⚠️  [4] 이미지 생성 실패 — 자리표시자로 대신합니다")
        else:
            print(f"   🖼️  [4] 로고 시안 1장 생성 ({source})")
        logos.append({"image_bytes": image, "prompt": prompt, "source": source})
    return logos


if __name__ == "__main__":
    # 한글 윈도우 콘솔(cp949)은 '—' 같은 글자에서 죽는다. 혼자 돌려 볼 때를 위한 안전장치.
    import sys
    for _stream in (sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8", errors="replace")

    from pathlib import Path

    brief_path = Path(__file__).resolve().parent / "samples" / "brief.json"
    sample = json.loads(brief_path.read_text(encoding="utf-8")) if brief_path.exists() else {}
    result = generate_logos(sample)
    for index, logo in enumerate(result, start=1):
        print(f"{index}. {len(logo['image_bytes'])} bytes ({logo['source']})")
        print(f"   {logo['prompt']}")
