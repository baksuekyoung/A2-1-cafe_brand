"""main.py 의 [1] 대화형 입력·검증.

명세가 요구하는 것 — `print` 와 `input` 으로 브리프 경로를 받고,
출력 폴더는 엔터를 치면 `./output` 을 쓴다.
검증 항목은 김준오님이 `#1단계` 에 정리한 목록을 그대로 따른다.
"""

import json
from pathlib import Path

import pytest

import main as main_module
from brand_result import runner


def _write(tmp_path: Path, name: str, text: str) -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


BRIEF = {
    "industry": "카페",
    "target": "20~30대 직장인",
    "keywords": ["여유", "따뜻함"],
}


def test_정상_브리프를_읽고_선택_필드를_채운다(tmp_path):
    path = _write(tmp_path, "brief.json", json.dumps(BRIEF, ensure_ascii=False))
    brief = main_module.load_brief(str(path))
    assert brief["industry"] == "카페"
    # 선택 필드는 [1] 이 기본값을 채워 넘긴다 — 뒤 단계가 매번 확인하지 않아도 되게.
    assert brief["tone"] == ""
    assert brief["competitors"] == []
    assert brief["notes"] == ""


def test_따옴표로_감싼_경로도_받는다(tmp_path):
    """탐색기에서 '경로로 복사' 하면 따옴표가 붙는다."""
    path = _write(tmp_path, "brief.json", json.dumps(BRIEF, ensure_ascii=False))
    assert main_module.load_brief(f'"{path}"')["industry"] == "카페"


def test_경로가_비면_거절한다():
    with pytest.raises(main_module.BriefError, match="경로를 입력"):
        main_module.load_brief("   ")


def test_json_확장자가_아니면_거절한다(tmp_path):
    path = _write(tmp_path, "brief.txt", "{}")
    with pytest.raises(main_module.BriefError, match="JSON 파일이 아닙니다"):
        main_module.load_brief(str(path))


def test_파일이_없으면_거절한다(tmp_path):
    with pytest.raises(main_module.BriefError, match="찾을 수 없습니다"):
        main_module.load_brief(str(tmp_path / "없는파일.json"))


def test_json_문법이_틀리면_몇번째_줄인지_알려준다(tmp_path):
    """쉼표가 남은 줄(2번째)을 가리켜야 고칠 수 있다."""
    path = _write(tmp_path, "brief.json", '{\n  "industry": "카페",\n}')
    with pytest.raises(main_module.BriefError, match="2번째 줄"):
        main_module.load_brief(str(path))


def test_객체가_아니면_거절한다(tmp_path):
    path = _write(tmp_path, "brief.json", '["카페"]')
    with pytest.raises(main_module.BriefError, match="객체여야"):
        main_module.load_brief(str(path))


def test_필수_필드가_없으면_어느_것인지_알려준다(tmp_path):
    path = _write(tmp_path, "brief.json", '{"industry": "카페"}')
    with pytest.raises(main_module.BriefError) as caught:
        main_module.load_brief(str(path))
    assert "target" in str(caught.value)
    assert "keywords" in str(caught.value)


def test_keywords_가_리스트가_아니면_거절한다(tmp_path):
    path = _write(tmp_path, "brief.json",
                  '{"industry": "카페", "target": "직장인", "keywords": "여유"}')
    with pytest.raises(main_module.BriefError, match="list 가 아닙니다"):
        main_module.load_brief(str(path))


def test_출력_폴더는_엔터를_치면_기본값(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _prompt="": "")
    assert main_module.ask_output() == "./output"


def test_출력_폴더를_적으면_그것을_쓴다(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _prompt="": '  "./결과"  ')
    assert main_module.ask_output() == "./결과"


def test_잘못된_경로를_주면_다시_묻는다(tmp_path, monkeypatch, capsys):
    """한 번 틀렸다고 프로그램이 죽으면 안 된다."""
    good = _write(tmp_path, "brief.json", json.dumps(BRIEF, ensure_ascii=False))
    answers = iter(["없는파일.json", str(good)])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    assert main_module.ask_brief()["industry"] == "카페"
    assert "찾을 수 없습니다" in capsys.readouterr().out


def test_브리프를_넘기면_step1_파일을_읽지_않는다():
    """main.py 가 [1] 을 끝내고 넘긴 경우, runner 는 그 값을 그대로 쓴다."""
    results = runner.run_all(brief=BRIEF)
    assert results[0].status == "ok"
    assert results[0].value is BRIEF


def test_넘겨받은_브리프도_규격_검사를_거친다():
    """어느 경로로 들어왔든 계약은 같다."""
    results = runner.run_all(brief={"industry": "카페"})
    assert results[0].status == "ok"       # 버리지는 않는다
    assert results[0].problems             # 어긋난 곳은 기록한다
