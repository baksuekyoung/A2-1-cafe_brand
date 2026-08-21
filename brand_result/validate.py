"""단계 결과가 데이터 계약을 지켰는지 검사한다.

`docs/데이터-계약.md` 가 규격 원문이고, 이 파일은 그 규격을 코드로 옮긴 것이다.
둘이 어긋나면 문서 쪽이 맞다고 본다.

검사는 **막지 않는다.** 어긋난 항목을 목록으로 돌려줄 뿐, 예외를 던지지 않는다.
팀원 파트가 아직 덜 끝난 상태에서도 통합을 돌려 봐야 하기 때문이다.
"""

from __future__ import annotations

import re

HEX_PATTERN = re.compile(r"^#[0-9A-F]{6}$")

MIN_KEYWORDS = 2
MIN_NAMES = 3
MIN_STORY_CHARS = 200
MIN_SUBS = 2


def _missing_keys(data: dict, keys: list[str], where: str) -> list[str]:
    return [f"{where}: '{key}' 키가 없습니다" for key in keys if key not in data]


def check_brief(brief: object) -> list[str]:
    """[1] 브랜드 브리프를 검사한다."""
    if not isinstance(brief, dict):
        return ["[1] brief 가 dict 가 아닙니다"]

    required = ["brand_name_hint", "industry", "target", "keywords", "tone", "extra"]
    problems = _missing_keys(brief, required, "[1] brief")

    keywords = brief.get("keywords")
    if isinstance(keywords, list):
        if len(keywords) < MIN_KEYWORDS:
            problems.append(
                f"[1] brief: keywords 가 {len(keywords)}개입니다 "
                f"({MIN_KEYWORDS}개 이상 필요)"
            )
    elif "keywords" in brief:
        problems.append("[1] brief: keywords 가 list 가 아닙니다")

    return problems


def check_naming(naming: object) -> list[str]:
    """[2] 네이밍·슬로건·스토리를 검사한다."""
    if not isinstance(naming, dict):
        return ["[2] naming 이 dict 가 아닙니다"]

    problems = _missing_keys(naming, ["names", "slogan", "story"], "[2] naming")

    names = naming.get("names")
    if isinstance(names, list):
        if len(names) < MIN_NAMES:
            problems.append(
                f"[2] naming: names 가 {len(names)}개입니다 ({MIN_NAMES}개 이상 필요)"
            )
        for index, item in enumerate(names, start=1):
            if not isinstance(item, dict):
                problems.append(f"[2] naming: names[{index}] 가 dict 가 아닙니다")
                continue
            problems += _missing_keys(item, ["name", "reason"], f"[2] naming.names[{index}]")
    elif "names" in naming:
        problems.append("[2] naming: names 가 list 가 아닙니다")

    story = naming.get("story")
    if isinstance(story, str) and len(story) < MIN_STORY_CHARS:
        problems.append(
            f"[2] naming: story 가 {len(story)}자입니다 ({MIN_STORY_CHARS}자 이상 필요)"
        )

    return problems


def _check_color(color: object, where: str) -> list[str]:
    if not isinstance(color, dict):
        return [f"{where} 가 dict 가 아닙니다"]

    problems = _missing_keys(color, ["hex", "name", "reason"], where)

    hex_value = color.get("hex")
    if isinstance(hex_value, str) and not HEX_PATTERN.match(hex_value):
        problems.append(
            f"{where}: hex 가 '{hex_value}' 입니다 — '#RRGGBB' 대문자 6자리로 주세요"
        )

    return problems


def check_palette(palette: object) -> list[str]:
    """[3] 컬러 팔레트를 검사한다."""
    if not isinstance(palette, dict):
        return ["[3] palette 가 dict 가 아닙니다"]

    problems = _missing_keys(palette, ["main", "subs"], "[3] palette")

    if "main" in palette:
        problems += _check_color(palette["main"], "[3] palette.main")

    subs = palette.get("subs")
    if isinstance(subs, list):
        if len(subs) < MIN_SUBS:
            problems.append(
                f"[3] palette: subs 가 {len(subs)}개입니다 ({MIN_SUBS}개 이상 필요)"
            )
        for index, sub in enumerate(subs, start=1):
            problems += _check_color(sub, f"[3] palette.subs[{index}]")
    elif "subs" in palette:
        problems.append("[3] palette: subs 가 list 가 아닙니다")

    return problems


def check_logos(logos: object) -> list[str]:
    """[4] 로고 시안을 검사한다."""
    if not isinstance(logos, list):
        return ["[4] logos 가 list 가 아닙니다"]

    problems: list[str] = []
    for index, logo in enumerate(logos, start=1):
        where = f"[4] logos[{index}]"
        if not isinstance(logo, dict):
            problems.append(f"{where} 가 dict 가 아닙니다")
            continue
        if "image_bytes" not in logo and "path" not in logo:
            problems.append(f"{where}: image_bytes 도 path 도 없습니다")
        if "prompt" not in logo:
            problems.append(f"{where}: 'prompt' 키가 없습니다")

    return problems
