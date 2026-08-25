"""[5] 에러 처리 통합 — 1~4단계를 불러 모으고, 실패해도 멈추지 않는다.

핵심은 **팀원 파트가 아직 없어도 돌아가는 것**이다.
대면으로 모일 수 없는 상황이라, 각자 파트가 끝나는 시점이 다르다.
"다 모여야 처음 돌려 본다" 가 되면 막판에 한꺼번에 터진다.

그래서 없는 단계는 "없다"고 기록하고 넘어간다. 지금 당장 돌려 보면
누가 무엇을 아직 안 냈는지 `run_report.md` 에 그대로 나온다.
"""

from __future__ import annotations

import importlib
import traceback
from dataclasses import dataclass, field

from . import validate

# docs/데이터-계약.md 가 정한 파일명·함수명. 이 표가 계약의 코드 쪽 표현이다.
STEPS = (
    ("[1] 브리프", "step1_brief", "load_brief", validate.check_brief),
    ("[2] 네이밍·슬로건·스토리", "step2_naming", "generate_naming", validate.check_naming),
    ("[3] 컬러 팔레트", "step3_palette", "generate_palette", validate.check_palette),
    ("[4] 로고 시안", "step4_logo", "generate_logos", validate.check_logos),
)


@dataclass
class StepResult:
    """한 단계의 실행 결과. 성공이든 실패든 반드시 하나 만들어진다."""

    name: str
    status: str  # "ok" | "missing" | "failed" | "skipped"
    value: object = None
    message: str = ""
    problems: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.status == "ok"


def _load(module_name: str, func_name: str):
    """팀원이 낸 모듈에서 계약이 정한 함수를 꺼낸다.

    아직 파일이 없거나 함수 이름이 다르면 그 사실을 문장으로 돌려준다.
    ImportError 를 그대로 위로 던지면 통합 실행이 거기서 끝나 버린다.
    """
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        # 없는 게 이 파일 자신인지, 이 파일이 import 하는 다른 패키지인지 가른다.
        # 둘을 뭉뚱그리면 "requests 를 안 깔았다" 를 "파일을 안 냈다" 로 잘못 알리게 되고,
        # 팀원은 멀쩡한 파일을 다시 만들려고 한다.
        if exc.name == module_name:
            return None, f"{module_name}.py 가 아직 없습니다"
        return None, f"{module_name}.py 를 읽는 중 오류 (없는 모듈: {exc.name})"
    except Exception as exc:  # 남의 모듈이 import 중에 터지는 경우
        return None, f"{module_name}.py 를 읽는 중 오류 ({type(exc).__name__}): {exc}"

    func = getattr(module, func_name, None)
    if func is None:
        return None, f"{module_name}.py 에 {func_name}() 가 없습니다 (계약 문서 확인)"
    if not callable(func):
        return None, f"{module_name}.{func_name} 가 함수가 아닙니다"
    return func, ""


def run_step(label: str, module_name: str, func_name: str, checker, *args, debug: bool = False):
    """한 단계를 실행한다. 무슨 일이 있어도 StepResult 를 돌려준다."""
    func, problem = _load(module_name, func_name)
    if func is None:
        return StepResult(label, "missing", message=problem)

    try:
        value = func(*args)
    except Exception as exc:
        if debug:
            traceback.print_exc()
        return StepResult(label, "failed", message=f"{type(exc).__name__}: {exc}")

    # 규격을 지켰는지 센다. 어긋나도 버리지 않는다 — 사람이 보고 판단할 문제다.
    problems = checker(value)
    return StepResult(label, "ok", value=value, problems=problems)


def run_all(*, brief: dict | None = None, debug: bool = False) -> list[StepResult]:
    """[1] → [4] 를 순서대로 실행한다. 앞이 무너져도 뒤를 시도한다.

    뒤 단계는 앞 결과를 인자로 받는다. 앞이 없으면 None 을 넘긴다 —
    계약 문서가 "앞 단계가 실패하면 그 자리는 비워 둔다" 고 정해 두었다.

    Args:
        brief: 이미 읽어 검증한 브리프. `main.py` 가 대화형으로 경로를 받아
            [1] 을 끝낸 뒤 넘긴다. 주면 `step1_brief.py` 를 부르지 않는다.
            규격 검사는 여기서 한 번 더 한다 — 어디로 들어왔든 계약은 같다.
    """
    results: list[StepResult] = []
    values: dict[str, object] = {}

    for index, (label, module_name, func_name, checker) in enumerate(STEPS):
        if index == 0 and brief is not None:
            result = StepResult(label, "ok", value=brief, problems=checker(brief))
            results.append(result)
            values["brief"] = brief
            continue

        # 계약이 정한 인자 순서: load_brief() / generate_naming(brief) /
        # generate_palette(brief, naming) / generate_logos(brief, naming, palette)
        args = [values.get(key) for key in ("brief", "naming", "palette")[:index]]
        result = run_step(label, module_name, func_name, checker, *args, debug=debug)
        results.append(result)
        if result.ok:
            values[("brief", "naming", "palette", "logos")[index]] = result.value

    return results


def to_result_dict(results: list[StepResult], generated_at: str) -> dict:
    """저장용 dict 로 옮긴다. 실패한 자리는 None 으로 남긴다."""
    keys = ("brief", "naming", "palette", "logos")
    payload: dict = {"generated_at": generated_at}
    payload.update({key: None for key in keys})

    for key, result in zip(keys, results):
        if result.ok:
            payload[key] = result.value

    payload["steps"] = [
        {
            "step": result.name,
            "status": result.status,
            "message": result.message,
            "problems": result.problems,
        }
        for result in results
    ]
    return payload
