"""API 연결 테스트.

    python test_api.py

간단한 메시지를 보내 API 키·인터넷·호출 권한이 정상인지 확인한다.
브랜드 생성을 돌리기 전에 이것부터 통과시키는 편이 빠르다.

`.env` 에 `CODYSSEY_OPENAI_KEY` · `OPENAI_API_KEY` · `GEMINI_API_KEY` 중
하나만 있으면 된다. 있는 것을 모두 확인하고, 이미지 생성까지 되는지도 본다.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

ENV_PATH = Path(__file__).resolve().parent / ".env"

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)
GEMINI_MODELS = ("gemini-flash-lite-latest", "gemini-flash-latest", "gemini-2.5-flash")
OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_MODELS = ("gpt-4o-mini", "gpt-4o")

# 코디세이 공개 API — 채팅은 OpenAI 규격이지만 response_format 을 받지 않는다.
CODYSSEY_BASE_URL = "https://copa.codyssey.kr"
CODYSSEY_MODELS = ("gpt-5-mini", "gemini-3-flash")
CODYSSEY_IMAGE_MODEL = "gpt-image-1-mini"   # 확인용이라 가장 저렴한 것으로

QUESTION = "안녕! 테스트야."

자리표시자 = {"", "your-api-key", "본인의_API_키", "sk-여기에본인키입력"}


def _load_env() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    try:
        load_dotenv(ENV_PATH)
    except Exception:
        pass  # .env 가 없어도 환경변수로 넣었을 수 있다


def _key(name: str) -> str:
    value = (os.environ.get(name) or "").strip()
    return "" if value in 자리표시자 else value


def check_codyssey(api_key: str, 이미지도: bool = False) -> tuple[bool, str]:
    """코디세이 공개 API 를 확인한다.

    콘솔에서 'Anthropic' 호환으로 발급한 키는 채팅에서 403 이 난다.
    그 경우를 알아볼 수 있게 응답을 그대로 보여 준다.

    Args:
        이미지도: True 면 이미지 생성까지 확인한다. **월 한도를 실제로 깎으므로**
            기본은 채팅만 본다. `--image` 로 켠다.
    """
    base = (os.environ.get("CODYSSEY_BASE_URL") or CODYSSEY_BASE_URL).rstrip("/")
    설명 = []

    채팅됨 = False
    시도 = []
    for model in CODYSSEY_MODELS:
        body = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": QUESTION}],
        }).encode("utf-8")
        try:
            with urllib.request.urlopen(_요청(f"{base}/v1/chat/completions", body, api_key),
                                        timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
            text = (payload["choices"][0]["message"]["content"] or "").strip()
            설명.append(f"채팅 {model} → {text[:24]}")
            채팅됨 = True
            break
        except urllib.error.HTTPError as exc:
            시도.append(f"{model}=HTTP {exc.code}")
        except Exception as exc:
            시도.append(f"{model}={type(exc).__name__}")
    if not 채팅됨:
        설명.append("채팅 실패(" + " / ".join(시도) + ")")

    if not 이미지도:
        설명.append("이미지 확인 생략(--image 로 켬)")
        return 채팅됨, " / ".join(설명)

    # 이미지는 로고 생성에 쓰므로 함께 본다. 호출 한 번이 한도에서 차감된다.
    body = json.dumps({
        "model": CODYSSEY_IMAGE_MODEL,
        "prompt": "a plain white square",
        "size": "1024x1024",
        "response_format": "b64_json",
    }).encode("utf-8")
    try:
        with urllib.request.urlopen(_요청(f"{base}/api/v1/images", body, api_key),
                                    timeout=90) as response:
            payload = json.loads(response.read().decode("utf-8"))
        크기 = len(payload["result"]["images"][0]["b64_json"])
        설명.append(f"이미지 OK({크기:,}자)")
        이미지됨 = True
    except urllib.error.HTTPError as exc:
        설명.append(f"이미지 HTTP {exc.code}")
        이미지됨 = False
    except Exception as exc:
        설명.append(f"이미지 {type(exc).__name__}")
        이미지됨 = False

    return (채팅됨 and 이미지됨), " / ".join(설명)


def _요청(url: str, body: bytes, api_key: str) -> urllib.request.Request:
    return urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {api_key}"},
        method="POST")


def check_openai(api_key: str) -> tuple[bool, str]:
    """`openai` 패키지 없이 표준 라이브러리로 부른다.

    설치 환경에 따라 그 패키지가 import 조차 안 되는 일이 있다.
    """
    시도 = []
    for model in OPENAI_MODELS:
        body = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": QUESTION}],
        }).encode("utf-8")
        request = urllib.request.Request(
            OPENAI_CHAT_URL,
            data=body,
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {api_key}"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
            text = (payload["choices"][0]["message"]["content"] or "").strip()
            return True, f"{model} → {text[:40]}"
        except urllib.error.HTTPError as exc:
            시도.append(f"{model}=HTTP {exc.code}")
        except Exception as exc:
            시도.append(f"{model}={type(exc).__name__}")
    return False, " / ".join(시도)


def check_gemini(api_key: str) -> tuple[bool, str]:
    body = json.dumps({"contents": [{"parts": [{"text": QUESTION}]}]}).encode("utf-8")
    시도 = []
    for model in GEMINI_MODELS:
        request = urllib.request.Request(
            GEMINI_URL.format(model=model),
            data=body,
            headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
            parts = payload["candidates"][0]["content"]["parts"]
            text = "".join(part.get("text", "") for part in parts).strip()
            return True, f"{model} → {text[:40]}"
        except urllib.error.HTTPError as exc:
            시도.append(f"{model}=HTTP {exc.code}")
        except Exception as exc:
            시도.append(f"{model}={type(exc).__name__}")
    return False, " / ".join(시도)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    _load_env()

    코디세이검사 = (lambda 키: check_codyssey(키, 이미지도=args.image))
    공급자 = [("코디세이", _key("CODYSSEY_OPENAI_KEY"), 코디세이검사),
              ("OpenAI", _key("OPENAI_API_KEY"), check_openai),
              ("Gemini", _key("GEMINI_API_KEY"), check_gemini)]

    있는키 = [(이름, 키, 검사) for 이름, 키, 검사 in 공급자 if 키]
    if not 있는키:
        print("❌ API 키가 없습니다.")
        print("   .env.example 을 .env 로 복사한 뒤")
        print("   CODYSSEY_OPENAI_KEY · OPENAI_API_KEY · GEMINI_API_KEY 중"
              " 하나를 채워 주십시오.")
        print()
        print("   키가 없어도 python main.py 는 예시 값으로 돌아갑니다.")
        return 1

    성공 = False
    for 이름, 키, 검사 in 있는키:
        됨, 설명 = 검사(키)
        print(f"  {'✅' if 됨 else '❌'} {이름}: {설명}")
        성공 = 성공 or 됨

    print()
    if 성공:
        print("✅ 연결 성공 — python main.py 를 돌리면 실제 결과가 나옵니다.")
        return 0
    print("❌ 키는 있으나 호출에 실패했습니다. 키 값과 결제·쿼터 상태를 확인해 주십시오.")
    return 1


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="API 키·인터넷·호출 권한이 정상인지 확인합니다.",
        epilog="기본은 채팅만 확인합니다. 이미지 확인은 월 한도를 깎으므로 --image 로 켭니다.")
    parser.add_argument("--image", action="store_true",
                        help="코디세이 이미지 생성까지 확인 (호출 1회가 한도에서 차감됨)")
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
