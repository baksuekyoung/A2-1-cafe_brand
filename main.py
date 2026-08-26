#!/usr/bin/env python3
"""브랜드 아이덴티티 생성기 — 진입점.

    python main.py                                   # 대화형 (명세가 요구하는 방식)
    python main.py --brief samples/brief.json        # 묻지 않고 바로
    python main.py --brief b.json --output out --logos 3

브리프 JSON 경로와 출력 폴더를 물어본 뒤, [1] 검증을 거쳐 [2]~[5] 로 넘긴다.

명세는 `print` 와 `input` 으로 받는 대화형을 요구하므로 그것이 기본이다.
인자는 같은 결과를 다시 만들어야 할 때(자동화·시연·채점 재현)를 위한 것이고,
준 인자만 묻지 않고 건너뛴다.

## [1] 처리 순서

    경로 입력 → 파일 존재 확인 → JSON 형식 확인 → 필수 필드 확인
    → 자료형 확인 → 선택 필드 기본값 적용 → 출력 폴더 생성 → 다음 단계 전달

규격은 `docs/데이터-계약.md` 의 [1] 절에 있다.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import integrate
from brand_result import validate

# 한국 Windows 콘솔은 cp949 라 이모지를 찍는 순간 죽는다. 표준 출력만 UTF-8 로 바꾼다.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_OUTPUT = "./output"

# 선택 필드에 채워 넣을 기본값. [1] 이 여기까지 끝내고 넘기므로
# 뒤 단계는 키가 있는지 매번 확인하지 않아도 된다.
OPTIONAL_DEFAULTS = {"tone": "", "competitors": [], "notes": ""}


class BriefError(Exception):
    """브리프를 읽거나 검증하는 중 생긴 문제. 메시지를 그대로 사람에게 보여 준다."""


def load_brief(path_text: str) -> dict:
    """브리프 JSON 을 읽어 검증한 뒤 계약 형식으로 돌려준다.

    Raises:
        BriefError: 경로가 비었거나, 파일이 없거나, JSON 이 깨졌거나,
            필수 필드가 없거나 자료형이 어긋난 경우.
    """
    path_text = path_text.strip().strip('"').strip("'")
    if not path_text:
        raise BriefError("파일 경로를 입력해 주십시오.")

    path = Path(path_text)
    if path.suffix.lower() != ".json":
        raise BriefError(f"JSON 파일이 아닙니다: {path.name}")
    if not path.exists():
        raise BriefError(f"파일을 찾을 수 없습니다: {path}")

    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise BriefError(f"파일을 읽지 못했습니다: {exc}") from exc

    try:
        brief = json.loads(raw)
    except json.JSONDecodeError as exc:
        # 쉼표나 괄호가 틀린 경우다. 몇 번째 줄인지 알려 줘야 고칠 수 있다.
        raise BriefError(f"JSON 형식이 잘못되었습니다 ({exc.lineno}번째 줄): {exc.msg}") from exc

    if not isinstance(brief, dict):
        raise BriefError("브리프는 중괄호로 감싼 객체여야 합니다.")

    problems = validate.check_brief(brief)
    if problems:
        raise BriefError("\n   - ".join(["브리프가 규격과 다릅니다."] + problems))

    for key, default in OPTIONAL_DEFAULTS.items():
        brief.setdefault(key, default)
    return brief


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """인자를 읽는다. 아무것도 안 주면 전부 대화형으로 묻는다."""
    parser = argparse.ArgumentParser(
        description="브랜드 브리프로 네이밍·슬로건·스토리·컬러·로고를 만듭니다.",
        epilog="인자를 생략하면 대화형으로 물어봅니다.")
    parser.add_argument("--brief", help="브리프 JSON 경로 (생략하면 물어봅니다)")
    parser.add_argument("--output",
                        help=f"출력 폴더 (생략하면 물어봅니다, 기본 {DEFAULT_OUTPUT})")
    parser.add_argument("--logos", type=int, choices=(2, 3),
                        help="로고 시안 수 (명세는 2~3장, 기본 2장)")
    return parser.parse_args(argv)


def ask_brief(path_text: str | None = None) -> dict:
    """올바른 브리프를 받을 때까지 다시 묻는다.

    Args:
        path_text: `--brief` 로 받은 경로. 주면 묻지 않는다.
            잘못된 경로면 그 자리에서 멈춘다 — 인자로 돌리는 쪽은 사람이
            지켜보고 있지 않으므로, 되물어 봐야 답할 사람이 없다.
    """
    if path_text is not None:
        try:
            return load_brief(path_text)
        except BriefError as exc:
            print(f"\n❌ {exc}\n")
            raise SystemExit(2)

    while True:
        try:
            answer = input("브리프 JSON 경로를 입력하세요: ")
        except (EOFError, KeyboardInterrupt):
            print("\n입력을 취소했습니다.")
            raise SystemExit(130)

        try:
            return load_brief(answer)
        except BriefError as exc:
            print(f"\n❌ {exc}\n")


def ask_output(path_text: str | None = None) -> str:
    """출력 폴더를 묻는다. 엔터를 치면 기본값을 쓴다.

    Args:
        path_text: `--output` 으로 받은 경로. 주면 묻지 않는다.
    """
    if path_text is not None:
        return path_text.strip().strip('"').strip("'") or DEFAULT_OUTPUT

    try:
        answer = input(f"출력 폴더 경로를 입력하세요 (엔터 시 {DEFAULT_OUTPUT}): ")
    except (EOFError, KeyboardInterrupt):
        print("\n입력을 취소했습니다.")
        raise SystemExit(130)
    return answer.strip().strip('"').strip("'") or DEFAULT_OUTPUT


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    print("\n🎨 브랜드 아이덴티티 생성기\n")

    if args.logos:
        # [4] 가 이 값을 읽는다. 계약이 정한 함수 서명을 건드리지 않으려는 것이다.
        os.environ["LOGO_COUNT"] = str(args.logos)

    brief = ask_brief(args.brief)
    print(f"   📋 {brief['industry']} · {brief['target']}")
    print(f"      키워드: {', '.join(brief['keywords'])}\n")

    return integrate.run(ask_output(args.output), brief=brief)


if __name__ == "__main__":
    sys.exit(main())
