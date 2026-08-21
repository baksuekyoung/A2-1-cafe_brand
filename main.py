#!/usr/bin/env python3
"""브랜드 아이덴티티 생성기 — 통합 실행 ([5] 담당 노희선).

    python main.py                # 있는 파트만 모아 결과를 낸다
    python main.py --output out   # 출력 폴더 지정
    python main.py --debug        # 실패한 단계의 전체 추적을 출력

팀원 파트가 아직 없어도 돌아간다. 무엇이 없는지 `run_report.md` 에 적힌다.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from brand_result import report, runner, store

# 한국 Windows 콘솔은 cp949 라 이모지를 찍는 순간 죽는다. 표준 출력만 UTF-8 로 바꾼다.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

MARK = {"ok": "✅", "missing": "⬜", "failed": "❌", "skipped": "↷"}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="1~4단계 결과를 모아 저장합니다.")
    parser.add_argument("--output", default="./output", help="출력 폴더 (기본값 ./output)")
    parser.add_argument("--debug", action="store_true", help="실패한 단계의 전체 추적을 출력")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    print("\n🎨 브랜드 아이덴티티 — 결과 통합\n")

    try:
        output_dir = store.ensure_output_dir(args.output)
    except OSError as exc:
        print(f"❌ 출력 폴더를 만들 수 없습니다: {exc}")
        return 2

    results = runner.run_all(debug=args.debug)
    for result in results:
        note = result.message or (f"규격 확인 필요 {len(result.problems)}건" if result.problems else "")
        print(f"  {MARK.get(result.status, '?')} {result.name}" + (f" — {note}" if note else ""))

    payload = runner.to_result_dict(results, datetime.now().isoformat(timespec="seconds"))

    # 로고는 파일로 먼저 떨구고, JSON 에는 파일명만 남긴다.
    logo_paths = []
    if isinstance(payload.get("logos"), list):
        try:
            logo_paths = store.save_logos(payload["logos"], output_dir)
        except OSError as exc:
            print(f"  ⚠️  로고 저장 실패: {exc}")

    saved = []
    writers = (
        ("brand_result.json", lambda: store.save_json(report.strip_bytes(payload), output_dir)),
        ("brand_result.md", lambda: _write(output_dir / "brand_result.md", report.build_markdown(payload))),
        ("run_report.md", lambda: _write(output_dir / "run_report.md", report.build_run_report(payload))),
    )
    if isinstance(payload.get("palette"), dict):
        writers += (("brand_tokens.css", lambda: store.save_css_tokens(payload["palette"], output_dir)),)

    print()
    for label, write in writers:
        try:
            path = write()
        except OSError as exc:
            print(f"  ❌ {label} 저장 실패 — {exc}")
        else:
            saved.append(path)
            print(f"  💾 {path}")

    for path in logo_paths:
        print(f"  💾 {path}")

    if not saved:
        print("\n❌ 결과를 한 건도 저장하지 못했습니다. 폴더 권한과 남은 용량을 확인하세요.")
        return 1

    done = sum(1 for result in results if result.ok)
    print(f"\n{'✅' if done else '⚠️ '} 완료 단계 {done}/4 · {output_dir}")
    if done < len(results):
        print("   아직 안 들어온 파트는 run_report.md 를 보세요.")
    return 0


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


if __name__ == "__main__":
    sys.exit(main())
