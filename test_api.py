"""API 연결 테스트.

    python test_api.py

간단한 메시지를 보내 API 키·인터넷·호출 권한이 정상인지 확인한다.
브랜드 생성을 돌리기 전에 이것부터 통과시키는 편이 빠르다.
"""

import os
import sys

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


def main() -> int:
    try:
        from dotenv import load_dotenv
        from openai import OpenAI
    except ImportError as exc:
        print(f"❌ 패키지가 없습니다 ({exc.name})")
        print("   pip install -r requirements.txt")
        return 1

    load_dotenv()
    api_key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if not api_key or api_key == "본인의_API_키":
        print("❌ OPENAI_API_KEY 가 없습니다.")
        print("   .env.example 을 .env 로 복사한 뒤 키를 채워 주십시오.")
        return 1

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "안녕! 테스트야."}],
            timeout=30,
        )
    except Exception as exc:
        print(f"❌ 호출에 실패했습니다: {type(exc).__name__}: {exc}")
        return 1

    print("✅ 연결 성공")
    print(f"   응답: {response.choices[0].message.content}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
