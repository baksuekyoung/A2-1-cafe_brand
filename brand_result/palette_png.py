"""컬러 팔레트를 PNG 로 시각화한다.

명세가 요구하는 산출물이다.

> matplotlib 등 다양한 방법으로 컬러 팔레트를 시각화하여 PNG로 저장한다.

**matplotlib 이 있으면 쓰고, 없으면 직접 PNG 를 만든다.**
[5] 통합 파트는 외부 패키지 없이 돌아가는 것이 약속이라, 팀원 중 누구든
설치 없이 실행해도 팔레트 이미지가 나와야 한다.

직접 만드는 쪽은 `zlib` 과 `struct` 만 쓴다. 둘 다 표준 라이브러리다.
글자는 아래 5x7 비트맵으로 찍는다 — HEX 코드는 ASCII 라 폰트 파일이 필요 없다.
(한글 이름은 `brand_result.md` 에 들어가므로 이미지에는 HEX 만 넣는다.)
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

WIDTH = 900
MAIN_HEIGHT = 220
SUB_HEIGHT = 150
PADDING = 24
SCALE = 3  # 5x7 글자를 3배로 키운다

# 5x7 비트맵. HEX 코드에 쓰이는 글자만 있으면 된다.
FONT = {
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    "?": ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
}

GLYPH_WIDTH, GLYPH_HEIGHT = 5, 7


def _rgb(hex_color: str) -> tuple[int, int, int]:
    """'#2F4858' 을 (47, 72, 88) 로. 읽을 수 없으면 중간 회색."""
    text = str(hex_color or "").strip().lstrip("#")
    if len(text) != 6:
        return (128, 128, 128)
    try:
        return (int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16))
    except ValueError:
        return (128, 128, 128)


def _text_color(rgb: tuple[int, int, int]) -> tuple[int, int, int]:
    """배경이 밝으면 검정, 어두우면 흰색. 글자가 안 보이면 소용이 없다."""
    red, green, blue = rgb
    return (0, 0, 0) if (0.299 * red + 0.587 * green + 0.114 * blue) > 150 else (255, 255, 255)


def _draw_text(pixels: list[bytearray], text: str, x: int, y: int,
               color: tuple[int, int, int]) -> None:
    """비트맵 글자를 픽셀 버퍼에 찍는다. 화면 밖으로 나가는 부분은 버린다."""
    height = len(pixels)
    width = len(pixels[0]) // 3 if height else 0

    for char in text.upper():
        glyph = FONT.get(char, FONT["?"])
        for row in range(GLYPH_HEIGHT):
            for col in range(GLYPH_WIDTH):
                if glyph[row][col] != "1":
                    continue
                for dy in range(SCALE):
                    py = y + row * SCALE + dy
                    if not 0 <= py < height:
                        continue
                    for dx in range(SCALE):
                        px = x + col * SCALE + dx
                        if not 0 <= px < width:
                            continue
                        pixels[py][px * 3:px * 3 + 3] = bytes(color)
        x += (GLYPH_WIDTH + 1) * SCALE


def _fill(pixels: list[bytearray], x0: int, y0: int, x1: int, y1: int,
          color: tuple[int, int, int]) -> None:
    row = bytes(color) * max(0, x1 - x0)
    for y in range(max(0, y0), min(len(pixels), y1)):
        pixels[y][x0 * 3:x1 * 3] = row


def _encode_png(pixels: list[bytearray]) -> bytes:
    """RGB 픽셀 버퍼를 PNG 바이트로 만든다."""
    height = len(pixels)
    width = len(pixels[0]) // 3 if height else 0

    # 각 줄 앞에 필터 바이트 0(= 필터 없음)을 붙이는 것이 PNG 규격이다.
    raw = b"".join(b"\x00" + bytes(row) for row in pixels)

    def chunk(tag: bytes, data: bytes) -> bytes:
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)  # 8bit RGB
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", header)
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))


def _colors(palette: dict) -> tuple[dict, list[dict]]:
    main = palette.get("main") if isinstance(palette.get("main"), dict) else {}
    subs = [sub for sub in (palette.get("subs") or []) if isinstance(sub, dict)]
    return main or {}, subs


def _render_with_matplotlib(palette: dict, target: Path) -> bool:
    """matplotlib 이 있으면 이름까지 넣은 그림을 그린다. 없으면 False."""
    try:
        import matplotlib
        matplotlib.use("Agg")  # 화면 없는 환경에서도 돌아야 한다
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle
    except ImportError:
        return False

    main, subs = _colors(palette)
    entries = ([main] if main else []) + subs
    if not entries:
        return False

    # 한글 이름이 네모로 깨지지 않게, 있는 폰트 중 하나를 골라 쓴다.
    for family in ("Malgun Gothic", "AppleGothic", "NanumGothic", "Noto Sans CJK KR"):
        try:
            matplotlib.font_manager.findfont(family, fallback_to_default=False)
        except Exception:
            continue
        plt.rcParams["font.family"] = family
        break
    plt.rcParams["axes.unicode_minus"] = False

    figure, axes = plt.subplots(figsize=(len(entries) * 2.4, 3.4))
    for index, entry in enumerate(entries):
        hex_code = str(entry.get("hex", "#808080"))
        axes.add_patch(Rectangle((index, 0), 1, 1, facecolor=hex_code, edgecolor="white", lw=2))
        text_color = "#000000" if _text_color(_rgb(hex_code)) == (0, 0, 0) else "#FFFFFF"
        axes.text(index + 0.5, 0.60, str(entry.get("name", "")), ha="center", va="center",
                  color=text_color, fontsize=11)
        axes.text(index + 0.5, 0.40, hex_code.upper(), ha="center", va="center",
                  color=text_color, fontsize=10, family="monospace")
        axes.text(index + 0.5, -0.12, "메인" if index == 0 and main else f"서브 {index}",
                  ha="center", va="center", fontsize=9, color="#555555")

    axes.set_xlim(0, len(entries))
    axes.set_ylim(-0.25, 1)
    axes.axis("off")
    figure.savefig(target, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    return True


def _render_builtin(palette: dict, target: Path) -> None:
    """표준 라이브러리만으로 팔레트 PNG 를 만든다."""
    main, subs = _colors(palette)
    height = PADDING * 2 + MAIN_HEIGHT + (SUB_HEIGHT if subs else 0)

    white = (255, 255, 255)
    pixels = [bytearray(bytes(white) * WIDTH) for _ in range(height)]

    main_rgb = _rgb(main.get("hex", "#808080"))
    _fill(pixels, PADDING, PADDING, WIDTH - PADDING, PADDING + MAIN_HEIGHT, main_rgb)
    _draw_text(pixels, str(main.get("hex", "")).upper(),
               PADDING + 20, PADDING + 20, _text_color(main_rgb))

    if subs:
        top = PADDING + MAIN_HEIGHT
        span = (WIDTH - PADDING * 2) // len(subs)
        for index, sub in enumerate(subs):
            left = PADDING + span * index
            right = left + span if index < len(subs) - 1 else WIDTH - PADDING
            rgb = _rgb(sub.get("hex", "#808080"))
            _fill(pixels, left, top, right, top + SUB_HEIGHT, rgb)
            _draw_text(pixels, str(sub.get("hex", "")).upper(),
                       left + 16, top + 16, _text_color(rgb))

    target.write_bytes(_encode_png(pixels))


def save_palette_png(palette: dict, output_dir: Path) -> Path:
    """컬러 팔레트를 `color_palette.png` 로 저장한다.

    Raises:
        OSError: 파일을 쓸 수 없는 경우. 호출부가 잡아 리포트에 남긴다.
    """
    target = output_dir / "color_palette.png"
    if not _render_with_matplotlib(palette, target):
        _render_builtin(palette, target)
    return target
