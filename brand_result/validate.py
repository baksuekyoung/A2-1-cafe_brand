"""단계 결과가 데이터 계약을 지켰는지 검사한다.

`docs/데이터-계약.md` 가 규격 원문이고, 이 파일은 그 규격을 코드로 옮긴 것이다.
둘이 어긋나면 문서 쪽이 맞다고 본다.

검사는 **막지 않는다.** 어긋난 항목을 목록으로 돌려줄 뿐, 예외를 던지지 않는다.
팀원 파트가 아직 덜 끝난 상태에서도 통합을 돌려 봐야 하기 때문이다.
"""

from __future__ import annotations

import re

HEX_PATTERN = re.compile(r"^#[0-9A-F]{6}$")

REQUIRED_BRIEF_KEYS = ["industry", "target", "keywords"]
OPTIONAL_BRIEF_KEYS = ["tone", "competitors", "notes"]

MIN_KEYWORDS = 2
MIN_NAMES = 3
MAX_NAMES = 5  # 명세: 브랜드명 후보 3~5개
MIN_SLOGANS = 3
MIN_STORY_CHARS = 260  # 명세: 브랜드 스토리 300자 내외
MIN_SUBS = 2


def _missing_keys(data: dict, keys: list[str], where: str) -> list[str]:
    return [f"{where}: '{key}' 키가 없습니다" for key in keys if key not in data]


def check_brief(brief: object) -> list[str]:
    """[1] 브랜드 브리프를 검사한다.

    규격은 `docs/데이터-계약.md` 의 [1] 절을 따른다.
    선택 필드는 [1] 에서 기본값을 채워 넘기므로, 여기서는 **타입만** 본다.
    """
    if not isinstance(brief, dict):
        return ["[1] brief 가 dict 가 아닙니다"]

    problems = _missing_keys(brief, REQUIRED_BRIEF_KEYS, "[1] brief")

    # 키는 있는데 값이 비어 있으면 [2] 프롬프트가 빈칸으로 나간다. 잡아 둔다.
    for key in ("industry", "target"):
        value = brief.get(key)
        if isinstance(value, str) and not value.strip():
            problems.append(f"[1] brief: {key} 가 비어 있습니다")

    keywords = brief.get("keywords")
    if isinstance(keywords, list):
        if len(keywords) < MIN_KEYWORDS:
            problems.append(
                f"[1] brief: keywords 가 {len(keywords)}개입니다 "
                f"({MIN_KEYWORDS}개 이상 필요)"
            )
    elif "keywords" in brief:
        problems.append("[1] brief: keywords 가 list 가 아닙니다")

    # 선택 필드 — 없는 건 괜찮지만, 있는데 타입이 다르면 [2] 가 터진다.
    if "competitors" in brief and not isinstance(brief["competitors"], list):
        problems.append("[1] brief: competitors 가 list 가 아닙니다")
    for key in ("tone", "notes"):
        if key in brief and not isinstance(brief[key], str):
            problems.append(f"[1] brief: {key} 가 문자열이 아닙니다")

    return problems


def check_naming(naming: object) -> list[str]:
    """[2] 네이밍·슬로건·스토리를 검사한다."""
    if not isinstance(naming, dict):
        return ["[2] naming 이 dict 가 아닙니다"]

    problems = _missing_keys(naming, ["naming", "slogans", "story"], "[2] naming")

    names = naming.get("naming")
    if isinstance(names, list):
        if not MIN_NAMES <= len(names) <= MAX_NAMES:
            problems.append(
                f"[2] naming: naming 이 {len(names)}개입니다 "
                f"({MIN_NAMES}~{MAX_NAMES}개 필요)"
            )
        for index, item in enumerate(names, start=1):
            if not isinstance(item, dict):
                problems.append(f"[2] naming: naming[{index}] 가 dict 가 아닙니다")
                continue
            problems += _missing_keys(item, ["name", "meaning"], f"[2] naming.naming[{index}]")

            # 보너스로 '다국어 네이밍 지원' 을 택했으므로 영문 표기가 있어야 한다.
            # 없다고 버리지는 않는다 — run_report.md 에 적어 사람이 보게 한다.
            english = str(item.get("english") or "").strip()
            if not english:
                problems.append(
                    f"[2] naming.naming[{index}]: english (영문 표기) 가 비어 있습니다"
                )
            elif not english.replace(" ", "").isascii():
                problems.append(
                    f"[2] naming.naming[{index}]: english 에 영문이 아닌 글자가 있습니다"
                )
    elif "naming" in naming:
        problems.append("[2] naming: naming 이 list 가 아닙니다")

    # 명세가 슬로건 3개를 요구한다. 하나만 받으면 규격 미달이 된다.
    slogans = naming.get("slogans")
    if isinstance(slogans, list):
        if len(slogans) < MIN_SLOGANS:
            problems.append(
                f"[2] naming: slogans 가 {len(slogans)}개입니다 ({MIN_SLOGANS}개 필요)"
            )
        for index, item in enumerate(slogans, start=1):
            if not isinstance(item, str) or not item.strip():
                problems.append(f"[2] naming: slogans[{index}] 가 빈 문자열입니다")
    elif "slogans" in naming:
        problems.append("[2] naming: slogans 가 문자열 배열이어야 합니다")

    # 보너스 — 없어도 규격 미달이 아니다. 있는데 모양이 틀린 것만 잡는다.
    competitors = naming.get("competitors")
    if competitors is not None and not isinstance(competitors, list):
        problems.append("[2] naming: competitors 가 list 가 아닙니다")
    elif isinstance(competitors, list):
        for index, item in enumerate(competitors, start=1):
            if not isinstance(item, dict):
                problems.append(f"[2] naming: competitors[{index}] 가 dict 가 아닙니다")
            elif not str(item.get("differentiation") or "").strip():
                problems.append(
                    f"[2] naming: competitors[{index}] 에 differentiation 이 비어 있습니다"
                )

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
        if logo.get("source") == "placeholder":
            # 1x1 투명 PNG 다. 파일은 있으나 그림이 없다 — 제출 전에 알아야 한다.
            problems.append(
                f"{where}: 이미지 생성이 모두 실패해 자리표시자가 들어갔습니다"
                " (logo_prompts.md 의 문장으로 직접 만들어 교체하세요)")

    return problems
