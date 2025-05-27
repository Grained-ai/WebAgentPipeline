from modules.qc_problems import (ProblemBase,
                                 MissingEndProblem,
                                 ConsecutiveScrollsProblem,
                                 RedundantLaunchAppProblem)
from modules.webagent_data_utils import WebAgentFlow
from modules.llm_utils.check_if_goto_instruction import check_if_goto_instruction
from modules.qc_exceptions import FlowCheck
from typing import Optional


def check_missing_end_step(flow: WebAgentFlow) -> Optional[ProblemBase]:
    if not flow.steps:
        raise FlowCheck(f"No steps in flow: {flow.id}. Title: {flow.title}")

    last_step = flow.steps[-1]
    if (last_step.title or '').upper() != 'END':
        return MissingEndProblem(detail='The last step is not END')
    return None


def check_consecutive_scrolls(flow: WebAgentFlow) -> Optional[ProblemBase]:
    if not flow.steps:
        raise FlowCheck(f"No steps in flow: {flow.id}. Title: {flow.title}")

    prev_scroll = False
    for step in flow.steps:
        if step.type == 'scroll':
            if prev_scroll:
                return ConsecutiveScrollsProblem(detail="Found consecutive scroll steps")
            prev_scroll = True
        else:
            prev_scroll = False
    return None


def check_if_redundant_first_launch_app(flow: WebAgentFlow) -> Optional[ProblemBase]:
    if_contain_goto, reason = check_if_goto_instruction(instruction=flow.title)
    if not if_contain_goto:
        return RedundantLaunchAppProblem(detail=reason, kwargs={"extra_note": reason, 'force': True})
    return None
