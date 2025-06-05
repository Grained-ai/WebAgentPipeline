import re

from modules.qc_problems import (ProblemBase,
                                 MissingEndProblem,
                                 ConsecutiveScrollsProblem,
                                 RedundantLaunchAppProblem,
                                 InstructionLevelWrongStepTypes)
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
    if prev_scroll:
        return ConsecutiveScrollsProblem(detail="Found consecutive scroll steps")
    return None


def check_if_redundant_first_launch_app(flow: WebAgentFlow) -> Optional[ProblemBase]:
    if flow.steps[0].type != 'launchApp':
        return None
    if flow.steps[0].deleted:
        return None
    if_contain_goto, reason = check_if_goto_instruction(instruction=flow.title)
    if not if_contain_goto:
        return RedundantLaunchAppProblem(detail=reason, kwargs={"extra_note": reason, 'force_delete': True})
    return None

def check_if_wrong_step_type(flow: WebAgentFlow) -> Optional[ProblemBase]:
    title_type_map = {'向.*滚动':'scroll',
                      '^ANSWER.*': 'answer',
                      '^END.*': 'end'}
    for step in flow.steps:
        for key in title_type_map.keys():
            if re.search(key, step.title.upper()) and step.type != title_type_map[key]:
                return InstructionLevelWrongStepTypes(detail='Got wrong step type.')
    return None