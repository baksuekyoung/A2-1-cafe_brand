"""저장과 문서 생성.

명세와 과정 규칙이 요구하는 것 — **평가는 코드와 마크다운만 본다.**
JSON 만 남기면 결과를 읽어 줄 사람이 없다.
"""

from __future__ import annotations

import json

import pytest
from conftest import LOGOS, PALETTE, PNG

import integrate as main_module
from brand_result import report, runner, store


# ---------------------------------------------------------------------------
# 저장
# ---------------------------------------------------------------------------


def test_이미지_바이트는_JSON_에_들어가지_않는다(tmp_path):
    """bytes 는 JSON 으로 직렬화되지 않는다. 그대로 두면 저장이 통째로 실패한다."""
    payload = {"generated_at": "t", "logos": list(LOGOS), "steps": []}
    cleaned = report.strip_bytes(payload)

    path = store.save_json(cleaned, store.ensure_output_dir(tmp_path))
    loaded = json.loads(path.read_text(encoding="utf-8"))

    assert "image_bytes" not in loaded["logos"][0]
    assert loaded["logos"][0]["prompt"] == "A minimal comma-shaped logo mark"
    assert payload["logos"][0]["image_bytes"] == PNG, "원본은 건드리지 않는다"


def test_로고는_두_자리_번호로_저장된다(tmp_path):
    saved = store.save_logos(list(LOGOS), store.ensure_output_dir(tmp_path))
    assert [path.name for path in saved] == ["logo_01.png", "logo_02.png"]
    assert saved[0].read_bytes() == PNG


def test_경로로_준_로고도_저장된다(tmp_path):
    """계약이 image_bytes 대신 path 도 허용한다."""
    source = tmp_path / "raw.png"
    source.write_bytes(PNG)
    saved = store.save_logos([{"path": str(source), "prompt": "p"}], store.ensure_output_dir(tmp_path / "out"))
    assert saved[0].read_bytes() == PNG


def test_한_장이_깨져도_나머지는_저장한다(tmp_path):
    logos = [{"prompt": "없는 파일", "path": str(tmp_path / "nope.png")}, LOGOS[0]]
    saved = store.save_logos(logos, store.ensure_output_dir(tmp_path / "out"))
    assert len(saved) == 1


def test_CSS_토큰이_팔레트를_그대로_옮긴다(tmp_path):
    text = store.save_css_tokens(PALETTE, store.ensure_output_dir(tmp_path)).read_text(encoding="utf-8")
    assert "--brand-main: #2F4858;" in text
    assert "--brand-sub-1: #F6F4F1;" in text
    assert "tailwind.config.js" in text


# ---------------------------------------------------------------------------
# 명도 대비
# ---------------------------------------------------------------------------


def test_명도_대비를_실제로_계산한다():
    """흰색과 검정의 대비는 21:1 이다 (WCAG 정의상 최댓값)."""
    assert store.contrast_ratio("#FFFFFF", "#000000") == 21.0


def test_대비가_모자라면_경고하되_막지_않는다():
    옅은_회색 = {"main": {"hex": "#CCCCCC", "name": "n", "reason": "r"}, "subs": []}
    warnings = store.check_contrast(옅은_회색)
    assert warnings and "흰 글씨" in warnings[0]


def test_hex_형식이_아니면_대비를_계산하지_않는다():
    """계약을 안 지킨 값에 계산을 들이대면 엉뚱한 예외가 난다."""
    assert store.check_contrast({"main": {"hex": "rgb(0,0,0)"}}) == []


# ---------------------------------------------------------------------------
# 문서
# ---------------------------------------------------------------------------


def test_결과_문서에_빈_자리가_드러난다(parts):
    parts(brief=True)
    payload = runner.to_result_dict(runner.run_all(), "2026-08-21T12:00:00")
    text = report.build_markdown(payload)

    assert "완료 단계 1/4" in text
    assert "성지순례 안내" in text
    assert text.count("_아직 없습니다._") == 3


def test_규격_위반이_문서에_남는다(parts):
    parts(
        brief=True,
        naming="def generate_naming(brief):\n    return {'naming': [], 'slogans': ['s'], 'story': '짧다'}\n",
    )
    payload = runner.to_result_dict(runner.run_all(), "t")
    text = report.build_run_report(payload)

    assert "규격이 어긋난 곳" in text
    assert "버리지 않고 저장했습니다" in text


def test_다_들어오면_문서에_전부_실린다(all_parts):
    payload = runner.to_result_dict(runner.run_all(), "2026-08-21T12:00:00")
    text = report.build_markdown(payload)

    assert "완료 단계 4/4" in text
    assert "쉼표" in text and "잠깐 멈추셔도 됩니다" in text
    assert "`#2F4858`" in text
    assert "logo_01.png" in text
    assert "_아직 없습니다._" not in text
    assert "모든 단계가 규격대로 끝났습니다" in report.build_run_report(payload)


# ---------------------------------------------------------------------------
# 통합 실행
# ---------------------------------------------------------------------------


def test_파트가_없어도_main_은_결과를_남긴다(tmp_path, parts, capsys):
    """[5] 의 가장 중요한 약속. 실행이 실패로 끝나면 안 된다."""
    parts()
    out = tmp_path / "output"
    assert main_module.main(["--output", str(out)]) == 0

    assert (out / "brand_result.json").exists()
    assert (out / "brand_result.md").exists()
    assert (out / "run_report.md").exists()
    assert "완료 단계 0/4" in capsys.readouterr().out


def test_다_들어오면_산출물이_전부_나온다(tmp_path, all_parts):
    out = tmp_path / "output"
    assert main_module.main(["--output", str(out)]) == 0

    for name in ("brand_result.json", "brand_result.md", "run_report.md",
                 "brand_tokens.css", "logo_01.png", "logo_02.png"):
        assert (out / name).exists(), f"{name} 이 없다"


def test_저장이_전부_실패하면_1_을_돌려준다(tmp_path, parts, monkeypatch):
    """조용히 0 을 돌려주면 자동화가 성공으로 오해한다."""
    parts()
    monkeypatch.setattr(store, "save_json", lambda *_a, **_k: (_ for _ in ()).throw(OSError("디스크 가득 참")))
    monkeypatch.setattr(main_module, "_write", lambda *_a, **_k: (_ for _ in ()).throw(OSError("권한 없음")))

    assert main_module.main(["--output", str(tmp_path / "out")]) == 1


# --- 화면 요약 --------------------------------------------------------------
#
# 명세의 실행 예시가 생성된 내용을 그 자리에서 보여 준다.
# 단계 성공 여부만 찍으면 돌린 사람이 파일을 열어 봐야 안다.

def test_네이밍_요약이_실제_내용을_보여_준다():
    줄 = report.summary_lines("[2] 네이밍·슬로건·스토리", {
        "naming": [{"name": "쉼표", "english": "Comma", "meaning": "잠깐 멈춤"},
                   {"name": "온기", "english": "Ongi", "meaning": "따뜻함"}],
        "slogans": ["가나다", "라마바", "사아자"],
        "story": "이" * 300,
        "competitors": [{"competitor": "블루보틀"}],
    })
    묶음 = "\n".join(줄)
    assert "쉼표 (Comma)" in 묶음        # 첫 후보는 뜻까지
    assert "잠깐 멈춤" in 묶음
    assert "온기 (Ongi)" in 묶음         # 나머지는 이름만
    assert "가나다" in 묶음 and "사아자" in 묶음   # 슬로건 셋 다
    assert "300자" in 묶음               # 스토리는 길이만
    assert "블루보틀" in 묶음


def test_팔레트_요약이_hex_와_이름을_보여_준다():
    줄 = report.summary_lines("[3] 컬러 팔레트", {
        "main": {"hex": "#2F4858", "name": "미드나이트 블루"},
        "subs": [{"hex": "#F6F4F1", "name": "웜 화이트"}],
    })
    묶음 = "\n".join(줄)
    assert "#2F4858" in 묶음 and "미드나이트 블루" in 묶음
    assert "#F6F4F1" in 묶음


def test_로고_요약이_출처를_센다():
    줄 = report.summary_lines("[4] 로고 시안", [
        {"source": "codyssey"}, {"source": "codyssey"}, {"source": "pollinations"},
    ])
    묶음 = "\n".join(줄)
    assert "3장" in 묶음
    assert "2장 codyssey" in 묶음 and "1장 pollinations" in 묶음


def test_자리표시자가_섞이면_경고한다():
    """파일은 있으나 그림이 없다. 돌린 사람이 알아야 한다."""
    줄 = report.summary_lines("[4] 로고 시안", [{"source": "placeholder"}])
    assert any("자리표시자" in l for l in 줄)


def test_형태가_어긋나면_조용히_넘어간다():
    """앞 단계가 실패하면 None 이 온다. 요약 때문에 죽으면 안 된다."""
    for 이름 in ("[2] 네이밍", "[3] 컬러", "[4] 로고"):
        assert report.summary_lines(이름, None) == []
    assert report.summary_lines("[1] 브리프", {"industry": "카페"}) == []
