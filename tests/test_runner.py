"""[5] 의 핵심 약속을 시험한다.

이 파트가 지켜야 할 것은 하나다 — **무슨 일이 있어도 결과를 남긴다.**
팀원 파트가 없어도, 남의 코드가 터져도, 규격이 어긋나도 저장은 된다.
"""

from __future__ import annotations

import json

import pytest
from conftest import PALETTE

from brand_result import report, runner, store


def test_파트가_하나도_없어도_결과가_저장된다(tmp_path, parts):
    """대면으로 모일 수 없으니 각자 파트가 끝나는 시점이 다르다.

    '다 모여야 처음 돌려 본다' 가 되면 막판에 한꺼번에 터진다.
    """
    parts()  # 아무것도 만들지 않는다
    results = runner.run_all()

    assert len(results) == 4
    assert all(result.status == "missing" for result in results)
    for result in results:
        assert ".py 가 아직 없습니다" in result.message


def test_없는_파트는_run_report_에_이름이_적힌다(parts):
    """팀원이 자기 파일명을 그대로 보고 무엇을 내야 하는지 알 수 있어야 한다."""
    parts(step1_brief=True)
    payload = runner.to_result_dict(runner.run_all(), "2026-08-21T12:00:00")
    text = report.build_run_report(payload)

    assert "step2_naming.py" in text
    assert "step3_palette.py" in text
    assert "step4_logo.py" in text
    assert "데이터-계약.md" in text


def test_일부만_있어도_있는_것은_저장된다(parts):
    parts(step1_brief=True, step2_naming=True)
    results = runner.run_all()

    assert [result.status for result in results] == ["ok", "ok", "missing", "missing"]
    payload = runner.to_result_dict(results, "2026-08-21T12:00:00")
    assert payload["brief"]["industry"] == "성지순례 안내"
    assert payload["naming"]["slogan"] == "잠깐 멈추셔도 됩니다"
    assert payload["palette"] is None


def test_남의_코드가_터져도_뒤_단계는_진행한다(parts):
    """팀원 코드에서 예외가 나도 통합이 거기서 끝나면 안 된다."""
    parts(
        step1_brief=True,
        step2_naming="def generate_naming(brief):\n    raise RuntimeError('API 키 없음')\n",
        step3_palette=True,
    )
    results = runner.run_all()

    assert results[1].status == "failed"
    assert "API 키 없음" in results[1].message
    assert results[2].status == "ok", "2단계가 터져도 3단계는 돌아야 한다"


def test_import_중에_터지는_모듈도_잡는다(parts):
    """파일은 있는데 import 하는 순간 터지는 경우 (오타·빠진 패키지)."""
    parts(step1_brief="import 없는패키지\n")
    results = runner.run_all()

    assert results[0].status == "missing"
    assert "읽는 중 오류" in results[0].message


def test_함수_이름이_다르면_계약을_가리킨다(parts):
    """파일은 냈는데 함수명이 계약과 다른 경우."""
    parts(step1_brief="def get_brief():\n    return {}\n")
    results = runner.run_all()

    assert results[0].status == "missing"
    assert "load_brief() 가 없습니다" in results[0].message
    assert "계약" in results[0].message


def test_규격이_어긋나도_버리지_않고_기록한다(parts):
    """규격 위반은 사람이 보고 판단할 문제다. 값은 살려 둔다."""
    부족한_네이밍 = {
        "names": [{"name": "쉼표", "reason": "하나뿐"}],  # 3개 이상이어야 한다
        "slogan": "잠깐 멈추셔도 됩니다",
        "story": "짧다",  # 200자 이상이어야 한다
    }
    parts(
        step1_brief=True,
        step2_naming=f"def generate_naming(brief):\n    return {부족한_네이밍!r}\n",
    )
    results = runner.run_all()

    assert results[1].status == "ok", "규격 위반이어도 값은 살린다"
    assert results[1].value["slogan"] == "잠깐 멈추셔도 됩니다"
    assert any("names" in problem for problem in results[1].problems)
    assert any("story" in problem for problem in results[1].problems)


def test_뒤_단계는_앞_결과를_인자로_받는다(parts):
    """계약이 정한 인자 순서대로 넘어가야 서로 어긋나지 않는다."""
    parts(
        step1_brief=True,
        step2_naming=True,
        step3_palette=(
            "def generate_palette(brief, naming):\n"
            "    assert brief['industry'] == '성지순례 안내'\n"
            "    assert naming['slogan'] == '잠깐 멈추셔도 됩니다'\n"
            "    return {'main': {'hex': '#2F4858', 'name': 'n', 'reason': 'r'},\n"
            "            'subs': [{'hex': '#FFFFFF', 'name': 'n', 'reason': 'r'},\n"
            "                     {'hex': '#000000', 'name': 'n', 'reason': 'r'}]}\n"
        ),
    )
    assert runner.run_all()[2].status == "ok"


def test_앞이_없으면_None_을_넘긴다(parts):
    """앞 단계가 실패해도 뒤 단계는 시도한다. 계약이 그렇게 정해져 있다."""
    parts(
        step2_naming=(
            "def generate_naming(brief):\n"
            "    assert brief is None\n"
            "    return {'names': [{'name': 'a', 'reason': 'r'}] * 3,\n"
            "            'slogan': 's', 'story': '가' * 200}\n"
        )
    )
    results = runner.run_all()
    assert results[0].status == "missing"
    assert results[1].status == "ok"


def test_빠진_패키지를_없는_파일로_오해하지_않는다(parts):
    """팀원이 파일은 냈는데 필요한 패키지를 안 깔았을 때.

    둘을 뭉뚱그리면 "패키지를 안 깔았다" 가 "파일을 안 냈다" 로 잘못 전달되고,
    팀원은 멀쩡한 파일을 다시 만들려고 한다. 처음 구현이 실제로 이렇게 틀렸고,
    위의 test_import_중에_터지는_모듈도_잡는다 가 그것을 잡았다.
    """
    parts(step1_brief="import 없는패키지\n")
    message = runner.run_all()[0].message

    assert "없는 모듈: 없는패키지" in message
    assert "아직 없습니다" not in message, "파일은 분명히 있다"


def test_파일이_진짜_없을_때는_없다고_한다(parts):
    """위 구분이 원래 메시지를 망가뜨리지 않았는지 확인한다."""
    parts()
    assert "step1_brief.py 가 아직 없습니다" in runner.run_all()[0].message
