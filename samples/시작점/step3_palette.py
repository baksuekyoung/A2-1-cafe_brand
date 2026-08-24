"""[3] 컬러 팔레트 — 담당: 미정

LLM 에게 브랜드에 맞는 색을 고르게 합니다.

지금은 예시 값이 고정으로 들어 있습니다.
"""

import json

# 계약이 요구하는 것 — 메인 1개, 서브 2개 이상. hex 는 '#RRGGBB' 대문자
EXAMPLE = {
    "main": {"hex": "#3E3028", "name": "로스팅 브라운", "reason": "원두를 볶은 색에서 가져왔습니다"},
    "subs": [
        {"hex": "#F5F0E8", "name": "크림", "reason": "여백을 만들고 글자를 읽기 쉽게 합니다"},
        {"hex": "#7C9070", "name": "세이지", "reason": "차분함을 더하는 포인트 색입니다"},
    ],
}


def generate_palette(brief: dict, naming: dict) -> dict:
    """docs/데이터-계약.md 의 [3] 규격대로 dict 를 돌려준다."""
    # 👉 여기를 채웁니다.
    #
    #    naming 도 함께 받습니다. 확정된 브랜드 이름과 스토리를 프롬프트에 넣어야
    #    글과 색이 따로 놀지 않습니다. naming 이 None 일 수도 있으니
    #    (앞 단계가 실패한 경우) 그때는 brief 만으로 만드세요.
    #
    #    hex 형식을 꼭 지키세요 — '#3E3028' ⭕ / '3e3028' ❌ / 'rgb(...)' ❌
    #    [5] 가 이 값으로 명도 대비를 계산합니다. 형식이 다르면 계산을 못 합니다.
    #
    #    프롬프트에 "hex 는 # 을 붙인 6자리 대문자로" 라고 적어 두면 잘 지킵니다.
    return EXAMPLE


if __name__ == "__main__":
    print(json.dumps(generate_palette({}, {}), ensure_ascii=False, indent=2))
