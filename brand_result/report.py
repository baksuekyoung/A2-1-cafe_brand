"""사람이 읽는 결과 문서를 만든다.

> **평가는 코드와 마크다운(.md) 문서만 본다.**

JSON 만 남기면 결과를 읽어 줄 사람이 없다. 터미널 출력도 마찬가지다.
`brand_result.md` 가 이 과제의 실질적인 제출물이다.
"""

from __future__ import annotations

from .store import check_contrast

STATUS_MARK = {"ok": "✅", "missing": "⬜", "failed": "❌", "skipped": "↷"}
STATUS_WORD = {
    "ok": "완료",
    "missing": "아직 없음",
    "failed": "실패",
    "skipped": "건너뜀",
}


def strip_bytes(payload: dict) -> dict:
    """JSON 으로 저장하기 전에 이미지 바이트를 뺀다.

    bytes 는 JSON 으로 직렬화되지 않는다. 파일로는 이미 저장했으니
    JSON 에는 파일명과 프롬프트만 남긴다.
    """
    logos = payload.get("logos")
    if not isinstance(logos, list):
        return payload

    payload = dict(payload)
    payload["logos"] = [
        {key: value for key, value in logo.items() if key != "image_bytes"}
        for logo in logos
        if isinstance(logo, dict)
    ]
    return payload


def build_run_report(payload: dict) -> str:
    """어느 단계가 되고 안 됐는지 한눈에 보이는 문서.

    대면으로 모이지 못하는 팀이라, 이 문서가 진행 상황 공유 수단이 된다.
    """
    lines = [
        "# 실행 리포트",
        "",
        f"실행 시각: {payload.get('generated_at', '')}",
        "",
        "| 단계 | 상태 | 비고 |",
        "| --- | :---: | --- |",
    ]

    for step in payload.get("steps", []):
        status = step.get("status", "")
        note = step.get("message", "")
        problems = step.get("problems") or []
        if problems:
            note = (note + " / " if note else "") + f"규격 확인 필요 {len(problems)}건"
        lines.append(
            f"| {step.get('step', '')} | {STATUS_MARK.get(status, '?')} "
            f"{STATUS_WORD.get(status, status)} | {note or '—'} |"
        )

    missing = [s for s in payload.get("steps", []) if s.get("status") == "missing"]
    failed = [s for s in payload.get("steps", []) if s.get("status") == "failed"]
    problems = [(s["step"], p) for s in payload.get("steps", []) for p in (s.get("problems") or [])]

    if missing:
        lines += ["", "## 아직 안 들어온 파트", ""]
        lines += [f"- {s['step']} — {s['message']}" for s in missing]
        lines += ["", "> 파일명과 함수명은 [`docs/데이터-계약.md`](../docs/데이터-계약.md) 를 따릅니다."]

    if failed:
        lines += ["", "## 실패한 파트", ""]
        lines += [f"- {s['step']} — {s['message']}" for s in failed]

    if problems:
        lines += ["", "## 규격이 어긋난 곳", "", "버리지 않고 저장했습니다. 사람이 보고 판단할 문제입니다.", ""]
        lines += [f"- **{step}** {problem}" for step, problem in problems]

    if not (missing or failed or problems):
        lines += ["", "모든 단계가 규격대로 끝났습니다."]

    return "\n".join(lines) + "\n"


def _brief_block(brief: dict | None) -> list[str]:
    if not isinstance(brief, dict):
        return ["_브리프가 아직 없습니다._", ""]
    rows = [
        ("업종", brief.get("industry")),
        ("타깃", brief.get("target")),
        ("키워드", ", ".join(brief.get("keywords") or [])),
        ("톤앤매너", brief.get("tone")),
    ]
    return (
        ["| 항목 | 내용 |", "| --- | --- |"]
        + [f"| {label} | {value or '—'} |" for label, value in rows]
        + [""]
    )


def _naming_block(naming: dict | None) -> list[str]:
    if not isinstance(naming, dict):
        return ["_아직 없습니다._", ""]

    lines = []
    names = naming.get("naming") or []
    if names:
        first = names[0]
        lines += [f"**{_full_name(first)}**", "", f"> {first.get('meaning', '')}", ""]
        if len(names) > 1:
            lines += ["다른 후보", ""]
            lines += [
                f"- {_full_name(item)} — {item.get('meaning', '')}" for item in names[1:]
            ]
            lines.append("")

    slogans = naming.get("slogans") or []
    if slogans:
        lines += ["### 슬로건", ""]
        lines += [f"> {s}" for s in slogans if isinstance(s, str)]
        lines.append("")

    story = naming.get("story")
    if story:
        lines += ["### 브랜드 스토리", "", story, "", f"*{len(story)}자*", ""]

    lines += _competitor_block(naming.get("competitors"))
    return lines or ["_내용이 비어 있습니다._", ""]


def _full_name(item: dict) -> str:
    """한글 이름에 영문 표기를 붙인다 (보너스 — 다국어 네이밍 지원).

    읽는 법이 있으면 함께 적는다. 영어권 사람에게 이름을 소개할 때 쓴다.
    """
    if not isinstance(item, dict):
        return ""
    name = str(item.get("name") or "").strip()
    english = str(item.get("english") or "").strip()
    reading = str(item.get("reading") or "").strip()

    if not english:
        return name
    영문 = f"{english}, {reading}" if reading else english
    return f"{name} ({영문})" if name else english


def _competitor_block(competitors: object) -> list[str]:
    """보너스 — 경쟁사별 차별화 포인트를 표로 낸다."""
    if not isinstance(competitors, list):
        return []  # [2] 가 엉뚱한 값을 줘도 문서 생성은 계속되어야 한다
    rows = [c for c in competitors if isinstance(c, dict) and c.get("competitor")]
    if not rows:
        return []

    lines = ["### 경쟁사 분석과 차별화 포인트", "",
             "| 경쟁사 | 시장에서의 자리 | 우리가 다르게 갈 지점 |",
             "| --- | --- | --- |"]
    for row in rows:
        cells = [str(row.get(key, "")).replace("|", "/")
                 for key in ("competitor", "position", "differentiation")]
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")
    return lines


def _palette_block(palette: dict | None) -> list[str]:
    if not isinstance(palette, dict):
        return ["_아직 없습니다._", ""]

    lines = ["| 역할 | HEX | 이름 | 고른 이유 |", "| --- | --- | --- | --- |"]
    main = palette.get("main") or {}
    lines.append(
        f"| 메인 | `{main.get('hex', '')}` | {main.get('name', '')} | {main.get('reason', '')} |"
    )
    for index, sub in enumerate(palette.get("subs") or [], start=1):
        if isinstance(sub, dict):
            lines.append(
                f"| 서브 {index} | `{sub.get('hex', '')}` | {sub.get('name', '')} "
                f"| {sub.get('reason', '')} |"
            )
    lines.append("")

    warnings = check_contrast(palette)
    if warnings:
        lines += ["**명도 대비 확인**", ""]
        lines += [f"- ⚠️ {warning}" for warning in warnings]
        lines += ["", "색을 고르는 건 사람의 판단이라 막지 않았습니다. 근거만 적어 둡니다.", ""]

    return lines


def _logo_block(logos: list | None) -> list[str]:
    if not isinstance(logos, list) or not logos:
        return ["_아직 없습니다._", ""]

    lines = []
    for index, logo in enumerate(logos, start=1):
        if not isinstance(logo, dict):
            continue
        lines += [f"### 시안 {index}", "", f"![로고 시안 {index}](logo_{index:02d}.png)", ""]
        prompt = logo.get("prompt")
        if prompt:
            lines += [f"프롬프트: `{prompt}`", ""]
    return lines


def build_markdown(payload: dict) -> str:
    """brand_result.md 본문을 만든다."""
    steps = {step.get("step", ""): step for step in payload.get("steps", [])}
    done = sum(1 for step in steps.values() if step.get("status") == "ok")

    lines = [
        "# 브랜드 아이덴티티 결과",
        "",
        f"생성 시각: {payload.get('generated_at', '')} · 완료 단계 {done}/4",
        "",
        "> 비어 있는 항목은 해당 파트가 아직 안 들어왔거나 실패한 것입니다.",
        "> 자세한 사유는 [`run_report.md`](run_report.md) 에 있습니다.",
        "",
        "---",
        "",
        "## 1. 브랜드 브리프",
        "",
        *_brief_block(payload.get("brief")),
        "---",
        "",
        "## 2. 네이밍 · 슬로건 · 스토리",
        "",
        *_naming_block(payload.get("naming")),
        "---",
        "",
        "## 3. 컬러 팔레트",
        "",
        *_palette_block(payload.get("palette")),
        "---",
        "",
        "## 4. 로고 시안",
        "",
        *_logo_block(payload.get("logos")),
    ]
    return "\n".join(lines) + "\n"
