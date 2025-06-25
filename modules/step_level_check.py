from modules.qc_problems import (
    ProblemBase,
    ChineseInTitleProblem,
    MissingBBoxProblem,
    VagueStepTitleProblem,
    MissingBlankScreenshotProblem,
    MissingMarkedScreenshotProblem,
    WrongStepTypeProblem,
    MissingQCImagePath,
    NeedVisualizeDelete,
    WrongScrollRect)
from modules.webagent_data_utils import WebAgentStep
from configs.configs import STORAGE_PATH
from loguru import logger
from typing import Optional
import re
from pathlib import Path


def check_chinese_in_title(step: WebAgentStep) -> Optional[ProblemBase]:
    if re.search(r"[\u4e00-\u9fff]", step.title or ""):
        return ChineseInTitleProblem(detail="Chinese characters in title")
    return None


def check_if_missing_bbox(step: WebAgentStep) -> Optional[ProblemBase]:
    if step.type not in ['press_enter', 'back', 'cache', 'paste', 'end', 'launchApp'] and step.title.lower() not in [
        'end']:
        if step.adjusted_rect is None:
            note = f'{step.type} missing adjusted_rect'

            if f'Need to add new bbox. Notes: {note}' in step.fix_methods:
                return None
            return MissingBBoxProblem(detail=f'{step.type} missing adjusted_rect',
                                      kwargs={"extra_note": note})
    return None


def check_if_answer(step: WebAgentStep) -> Optional[ProblemBase]:
    if step.type == 'answer':
        note = f'{step.type} need to manually add bbox'

        if f'Need to add new bbox. Notes: {note}' in step.fix_methods:
            return None
        if step.recrop_rect:
            return None
        return MissingBBoxProblem(detail=f'{step.type} need to manually add bbox',
                                  kwargs={"extra_note": note})
    return None


def check_if_vague_type_in(step: WebAgentStep) -> Optional[ProblemBase]:
    type_translation_map = {'paste': "Type in", 'type': "Type in",
                            'hover': "Hover over"}
    if step.type in ['type', 'hover', 'click', 'scroll', 'paste']:
        if not step.value:
            if step.title == f'{type_translation_map.get(step.type, step.type).capitalize()} {step.value}':
                return VagueStepTitleProblem(
                    detail='Title too vague for the step. Need to modify to <动作> <具体的元素>',
                    extra_note='Title too vague for the step. Need to modify to <动作> <具体的元素>')
    return None


def check_if_missing_frame(step: WebAgentStep) -> Optional[ProblemBase]:
    if not step.recording_id:
        logger.warning(f"No RecordingID for {step.id}: {step.type}")
        step.screenshot = None
        return None
    if not step.timestamp:
        logger.warning(f"No screenshot for {step.id}: {step.type}")
        step.screenshot = None
        return None
    if not step.screenshot:
        return MissingBlankScreenshotProblem(detail='Step screenshot is Empty.',
                                             kwargs={'storage_path': STORAGE_PATH})
    if not (Path(STORAGE_PATH) / step.screenshot).exists():
        return MissingBlankScreenshotProblem(detail=f'{(Path(STORAGE_PATH) / step.screenshot)} not exists.',
                                             kwargs={'storage_path': STORAGE_PATH})
    return None


def check_if_bbox_not_marked(step: WebAgentStep) -> Optional[ProblemBase]:
    if not step.timestamp:
        logger.warning(f"No screenshot for {step.id}: {step.type}")
        step.screenshot = None
        return None
    if not step.marked_screenshot:
        return MissingMarkedScreenshotProblem(detail='Step screenshot is Empty.',
                                              kwargs={'storage_path': STORAGE_PATH})
    if not (Path(STORAGE_PATH) / step.marked_screenshot).exists():
        return MissingMarkedScreenshotProblem(detail=f'{(Path(STORAGE_PATH) / step.marked_screenshot)} not exists.',
                                              kwargs={'storage_path': STORAGE_PATH})
    return None


# ADD CHECK STEP TYPE
def check_if_wrong_step_type(step: WebAgentStep) -> Optional[ProblemBase]:
    if step.type == 'paste':
        return WrongStepTypeProblem(detail='paste should be type in.')
    if step.type == 'type' and step.title.startswith('Input '):
        return WrongStepTypeProblem(detail='Input -> Type in')
    if step.type == 'hover' and not step.title.startswith('Hover over'):
        return WrongStepTypeProblem(detail='Hover -> Hover over')
    if step.title.upper().startswith('ANSWER') and step.type != 'answer':
        return WrongStepTypeProblem(detail='step.type -> answer')
    return None


def check_if_update_qc_image_used(step: WebAgentStep) -> Optional[ProblemBase]:
    if not step.qc_image_used:
        return MissingQCImagePath(detail='Refresh QC image used.',
                                  kwargs={'storage_path': STORAGE_PATH})
    return None


def check_if_visualize_delete_steps(step: WebAgentStep) -> Optional[ProblemBase]:
    if step.deleted and '[REMOVED]' not in step.title:
        return NeedVisualizeDelete(detail="Visualize delete steps.")
    return None

def check_if_scroll_in_full_screen(step: WebAgentStep) -> Optional[ProblemBase]:
    if step.type == 'scroll' and "whole screen" in step.title and not step.rect["top"]:
        return WrongScrollRect(detail='Modify Scroll Rect in full screen.',
                               kwargs={'storage_path': STORAGE_PATH})
    return None