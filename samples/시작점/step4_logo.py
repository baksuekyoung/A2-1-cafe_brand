"""[4] 로고 시안

이미지 생성 API 로 로고 시안을 2~3장 만들어 PNG 바이트로 돌려준다.

## 동작

    OPENAI_API_KEY 가 있으면   →  OpenAI 이미지 생성 API (gpt-image-1 → dall-e-3)
    없거나 실패하면            →  Pollinations (키 없이 쓸 수 있는 무료 API)
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
import urllib.request
from pathlib import Path

sys_path = str(Path(__file__).resolve().parent)
if sys_path not in __import__("sys").path:
    __import__("sys").path.insert(0, sys_path)

from brand_result import logo_prompt

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
POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}"

# 계정마다 열려 있는 모델이 다르다. 앞에서부터 시도해 먼저 되는 것을 쓴다.
OPENAI_MODELS = ("gpt-image-1", "dall-e-3")

LOGO_COUNT = 2  # 명세는 2~3장을 요구한다
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
                return base64.b64decode(item["b64_json"])
            if item.get("url"):
                with urllib.request.urlopen(item["url"], timeout=TIMEOUT) as image:
                    return image.read()
        except Exception:
            continue  # 이 모델은 못 쓴다. 다음 후보로.
    return None


def _pollinations_image(prompt: str) -> bytes | None:
    """키 없이 쓸 수 있는 무료 이미지 API. 마지막 보루다."""
    url = POLLINATIONS_URL.format(prompt=urllib.parse.quote(prompt))
    try:
        with urllib.request.urlopen(url + "?width=1024&height=1024&nologo=true",
                                    timeout=TIMEOUT) as response:
            data = response.read()
    except Exception:
        return None
    # PNG/JPEG 헤더가 아니면 오류 페이지를 받은 것이다. 그림인 척 저장하면 안 된다.
    return data if data[:4] == b"\x89PNG" or data[:2] == b"\xff\xd8" else None


def generate_logos(brief: dict, naming: dict | None = None,
                   palette: dict | None = None) -> list:
    """docs/데이터-계약.md 의 [4] 규격대로 list 를 돌려준다."""
    load_dotenv()
    api_key = (os.environ.get("OPENAI_API_KEY") or "").strip()

    logos = []
    for prompt in logo_prompt.make_prompts(brief or {}, naming, palette, LOGO_COUNT):
        image = _openai_image(prompt, api_key) if api_key else None
        source = "openai"
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
