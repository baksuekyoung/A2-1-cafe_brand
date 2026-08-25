"""테스트 공용 준비물.

각 단계(step1~4)를 진짜 파일 대신 임시 폴더에 만들어 넣었다가 치운다.
실제 통합이 어떻게 도는지 그대로 시험하려는 것이다.

저장소 루트에는 실제로 돌아가는 step*.py 가 있다. 막지 않으면 "파트가 아직
없을 때" 를 시험할 수 없으므로, 임시 폴더에 없는 단계는 없는 것으로 만든다.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

STEP_NAMES = ("step1_brief", "step2_naming", "step3_palette", "step4_logo")


class _BlockMissingParts:
    """임시 폴더에 없는 단계 모듈을 '없는 것' 으로 만든다.

    `sys.meta_path` 맨 앞에 꽂아 두면 import 를 가로챌 수 있다.
    `ModuleNotFoundError` 를 `name` 과 함께 던져야 통합 쪽이 "파일이 없다" 와
    "이 파일이 부르는 다른 패키지가 없다" 를 구분할 수 있다.
    """

    def __init__(self, part_dir: Path, names: set[str]) -> None:
        self.part_dir = part_dir
        self.names = names

    def find_spec(self, fullname, path=None, target=None):
        if fullname in self.names and not (self.part_dir / f"{fullname}.py").exists():
            raise ModuleNotFoundError(f"No module named {fullname!r}", name=fullname)
        return None  # 나머지는 평소대로


BRIEF = {
    "industry": "성지순례 안내",
    "target": "40-70대 신자와 조용한 여행을 찾는 20-30대",
    "keywords": ["고요", "순례", "치유"],
    "tone": "차분하고 경건한",
    "competitors": ["블루보틀"],
    "notes": "",
}

NAMING = {
    "naming": [
        {"name": "쉼표", "meaning": "문장을 잠시 멈추는 기호에서 따왔습니다"},
        {"name": "여백", "meaning": "비어 있음이 곧 쉼이라는 뜻입니다"},
        {"name": "한 모금", "meaning": "커피 한 모금의 짧은 휴식입니다"},
    ],
    "slogans": ["잠깐 멈추셔도 됩니다", "혼자여도 괜찮은 자리", "하루에 한 번, 쉼표"],
    "story": "하루에 한 번은 쉼표가 필요합니다. " * 12,
}

PALETTE = {
    "main": {"hex": "#2F4858", "name": "딥 네이비", "reason": "차분함을 위해 채도를 낮췄습니다"},
    "subs": [
        {"hex": "#F6F4F1", "name": "웜 화이트", "reason": "여백을 만듭니다"},
        {"hex": "#C9A227", "name": "머스터드", "reason": "포인트 색입니다"},
    ],
}

PNG = b"\x89PNG\r\n\x1a\n" + b"fake-image-bytes"
LOGOS = [
    {"image_bytes": PNG, "prompt": "A minimal comma-shaped logo mark"},
    {"image_bytes": PNG, "prompt": "A quiet stone path forming a circle"},
]


@pytest.fixture
def parts(tmp_path, monkeypatch):
    """팀원 파트를 임시로 만들어 import 경로에 올린다.

    `parts(step2_naming="...")` 처럼 소스를 직접 넣을 수도 있고,
    `parts(step1_brief=True)` 로 기본 구현을 넣을 수도 있다.
    """
    part_dir = tmp_path / "parts"
    part_dir.mkdir()
    monkeypatch.syspath_prepend(str(part_dir))

    # 저장소 루트의 진짜 step*.py 를 가린다. 이게 없으면 "파트가 없을 때" 를
    # 시험하는 테스트가 진짜 파일을 찾아내 전부 성공해 버린다.
    blocker = _BlockMissingParts(part_dir, set(STEP_NAMES))
    sys.meta_path.insert(0, blocker)
    monkeypatch.setattr(sys, "meta_path", sys.meta_path)  # 원상복구는 아래 finally 에서

    defaults = {
        "step1_brief": f"def load_brief():\n    return {BRIEF!r}\n",
        "step2_naming": f"def generate_naming(brief):\n    return {NAMING!r}\n",
        "step3_palette": f"def generate_palette(brief, naming):\n    return {PALETTE!r}\n",
        "step4_logo": f"def generate_logos(brief, naming, palette):\n    return {LOGOS!r}\n",
    }

    created: list[str] = []

    def make(**modules):
        for name, source in modules.items():
            if source is True:
                source = defaults[name]
            (part_dir / f"{name}.py").write_text(source, encoding="utf-8")
            created.append(name)
        # 앞선 테스트가 남긴 캐시를 쓰지 않게 한다
        importlib.invalidate_caches()
        for name in created:
            sys.modules.pop(name, None)
        return part_dir

    yield make

    if blocker in sys.meta_path:
        sys.meta_path.remove(blocker)
    for name in STEP_NAMES:
        sys.modules.pop(name, None)


@pytest.fixture
def all_parts(parts):
    """네 파트가 모두 갖춰진 정상 상태."""
    return parts(
        step1_brief=True, step2_naming=True, step3_palette=True, step4_logo=True
    )
