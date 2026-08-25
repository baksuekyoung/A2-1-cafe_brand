"""[5] 결과 저장 & 에러 처리 통합.

`docs/데이터-계약.md` 가 정한 형식대로 1~4단계 결과를 받아 파일로 낸다.
한 단계가 실패해도, 아직 안 들어왔어도 나머지는 저장한다.
"""

from .runner import STEPS, StepResult, run_all, to_result_dict
from .store import ensure_output_dir, save_css_tokens, save_json, save_logos

__all__ = [
    "STEPS",
    "StepResult",
    "run_all",
    "to_result_dict",
    "ensure_output_dir",
    "save_json",
    "save_logos",
    "save_css_tokens",
]
