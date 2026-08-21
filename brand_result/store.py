"""결과물을 파일로 저장한다.

명세가 요구하는 JSON·PNG 에 더해 `brand_result.md` 를 반드시 낸다.
**평가는 코드와 마크다운만 보기 때문에**, JSON 만 남기면 결과를 읽어 줄 사람이 없다.
"""

from __future__ import annotations

import json
from pathlib import Path

WCAG_AA_RATIO = 4.5


def ensure_output_dir(path: str | Path) -> Path:
    """출력 폴더를 만들고 경로를 돌려준다."""
    output = Path(path).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    return output


# ---------------------------------------------------------------- 명도 대비

def _channel(value: float) -> float:
    value /= 255
    return value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4


def relative_luminance(hex_color: str) -> float:
    """WCAG 상대 휘도. hex 는 '#RRGGBB' 형식이어야 한다."""
    raw = hex_color.lstrip("#")
    red, green, blue = (int(raw[i : i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _channel(red) + 0.7152 * _channel(green) + 0.0722 * _channel(blue)


def contrast_ratio(foreground: str, background: str) -> float:
    """두 색의 명도 대비를 돌려준다. 1.0 ~ 21.0."""
    light, dark = sorted(
        (relative_luminance(foreground), relative_luminance(background)), reverse=True
    )
    return round((light + 0.05) / (dark + 0.05), 2)


def check_contrast(palette: dict) -> list[str]:
    """메인 색과 흰색·검정의 대비를 재고, 기준 미달이면 경고를 돌려준다.

    막지는 않는다. 색을 고르는 건 사람의 판단이고, 여기서는 근거만 제공한다.
    """
    main = palette.get("main", {}).get("hex")
    if not isinstance(main, str) or not main.startswith("#"):
        return []

    warnings = []
    for label, other in (("흰 글씨", "#FFFFFF"), ("검은 글씨", "#000000")):
        ratio = contrast_ratio(main, other)
        if ratio < WCAG_AA_RATIO:
            warnings.append(
                f"메인 색 {main} 위 {label} 대비가 {ratio}:1 입니다 "
                f"(WCAG AA 기준 {WCAG_AA_RATIO}:1 미만)"
            )
    return warnings


# ---------------------------------------------------------------- 파일 저장

def save_json(result: dict, output_dir: Path) -> Path:
    """텍스트 결과 전체를 brand_result.json 으로 저장한다."""
    target = output_dir / "brand_result.json"
    target.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return target


def save_logos(logos: list, output_dir: Path) -> list[Path]:
    """로고 시안을 logo_01.png 형식으로 저장한다.

    image_bytes 가 있으면 그걸 쓰고, 없으면 path 의 파일을 복사한다.
    한 장이 실패해도 나머지는 저장한다.
    """
    saved: list[Path] = []
    for index, logo in enumerate(logos, start=1):
        if not isinstance(logo, dict):
            continue
        target = output_dir / f"logo_{index:02d}.png"
        data = logo.get("image_bytes")
        if not isinstance(data, (bytes, bytearray)):
            source = logo.get("path")
            if not source or not Path(source).is_file():
                continue
            data = Path(source).read_bytes()
        target.write_bytes(data)
        saved.append(target)
    return saved


def save_css_tokens(palette: dict, output_dir: Path) -> Path:
    """팔레트를 CSS 커스텀 프로퍼티와 Tailwind 색 설정으로 내보낸다.

    결과를 실제 웹 프로젝트로 옮길 때 HEX 를 손으로 베껴 적다가 오타가 난다.
    붙여 넣기만 하면 되는 형태로 만들어 둔다.
    """
    main = palette.get("main", {}).get("hex", "#000000")
    subs = [s for s in palette.get("subs", []) if isinstance(s, dict)]

    lines = [":root {", f"  --brand-main: {main};"]
    for index, sub in enumerate(subs, start=1):
        lines.append(f"  --brand-sub-{index}: {sub.get('hex', '#000000')};")
    lines += ["}", "", "/* Tailwind — tailwind.config.js 의 theme.extend.colors 에 붙여 넣기"]

    tailwind = {
        "brand": {
            "DEFAULT": main,
            **{
                f"sub{index}": sub.get("hex", "#000000")
                for index, sub in enumerate(subs, start=1)
            },
        }
    }
    lines += [json.dumps(tailwind, indent=2), "*/", ""]

    target = output_dir / "brand_tokens.css"
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
