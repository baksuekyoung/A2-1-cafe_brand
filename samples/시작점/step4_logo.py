"""[4] 로고 시안 — 담당: 이예은

이미지 생성 API 로 로고 시안을 2~3장 만듭니다.

지금은 진짜 이미지 대신 아주 작은 PNG 한 장이 들어 있습니다.
통합이 도는지 먼저 확인하고, 그 다음 `👉` 자리를 진짜 호출로 바꾸세요.
"""

import base64

# 1x1 투명 PNG. 자리만 채우는 용도입니다.
PLACEHOLDER = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def generate_logos(brief: dict, naming: dict, palette: dict) -> list:
    """docs/데이터-계약.md 의 [4] 규격대로 list 를 돌려준다."""
    # 👉 여기를 채웁니다.
    #
    #    ⚠️ 한국어를 이미지 API 에 그대로 넘기지 마세요.
    #       이전 과제에서 "20-30대 여성" 을 인물 사진 요청으로 읽어
    #       로고 자리에 사람 사진이 나온 적이 있습니다.
    #       LLM 에게 영어 장면 묘사를 먼저 시키고, 그것만 이미지 API 로 넘기세요.
    #
    #    ⚠️ 색은 hex 대신 색 이름을 넣으세요.
    #       이미지 모델은 '#3E3028' 을 거의 무시하고 '로스팅 브라운' 은 알아듣습니다.
    #       palette["main"]["name"] 을 쓰면 됩니다. (palette 가 None 일 수 있으니 확인하고)
    #
    #    ⚠️ 프롬프트를 짧게. 500자짜리를 넣으면 무료 모델이 흘려버립니다.
    #       100자 안팎이 잘 먹힙니다.
    #
    #    돌려줄 때는 image_bytes(PNG 원본) 또는 path(저장한 파일 경로) 중 하나면 됩니다.
    return [
        {"image_bytes": PLACEHOLDER, "prompt": "flat vector logo, a comma shape formed by a coffee bean, roasting brown, plain white background"},
        {"image_bytes": PLACEHOLDER, "prompt": "flat vector logo, a single cup seen from above with a sage green ring, minimal line art"},
    ]


if __name__ == "__main__":
    logos = generate_logos({}, {}, {})
    print(f"로고 {len(logos)}장 · 첫 장 {len(logos[0]['image_bytes'])} bytes")
