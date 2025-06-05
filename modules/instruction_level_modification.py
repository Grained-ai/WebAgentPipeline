import json
import re

from modules.qc_exceptions import FlowModification
from loguru import logger
from pathlib import Path
from modules.media_utils.video_ops import convert_webm_to_mp4, get_video_duration_ms, merge_scroll_group_in_place
from modules.general_utils import generate_random_id
from modules.webagent_data_utils import WebAgentFlow
from modules.step_level_modification import delete_step


def check_and_add_end_step(flow: WebAgentFlow, **kwargs) -> WebAgentFlow:
    storage_path = kwargs.get('storage_path')
    if not storage_path:
        raise FlowModification("Please provide storage path to function.")
    storage_path = Path(storage_path)
    recording_id = None
    for step in flow.steps:
        if step.recording_id:
            recording_id = step.recording_id
            break
    last_step = flow.steps[-1]

    if recording_id:
        webm_video_path = storage_path / f"{recording_id}.webm"
        mp4_video_path = storage_path / f"{recording_id}.mp4"

        if not webm_video_path.exists():
            raise FlowModification(f"Missing webm recording for RecordID: {recording_id}")

        if not mp4_video_path.exists():
            try:
                convert_webm_to_mp4(webm_video_path, mp4_video_path)
            except Exception as e:
                raise FlowModification(f"Recording conversion failed for RecordID: {recording_id}. Error: {e}")

        last_timestamp = get_video_duration_ms(mp4_video_path)
        if last_timestamp is not None:
            end_step_dict = {
                "id": generate_random_id(len(last_step.id)),
                "title": "end",
                "type": "click",
                "devicePixelRatio": last_step.device_pixel_ratio,
                "timestamp": int(last_timestamp),
                "viewport": last_step.viewport,
                "browserTopHeight": last_step.browser_top_height,
                "createdTime": last_step.created_time,
            }
            flow.to_dict()['steps'].append(end_step_dict)
            logger.warning(f"Added END step to flow {flow.id}. New step ID: {end_step_dict['id']}")
    else:
        logger.warning(f"No recordingId found in flow {flow.id}")

    return flow


def merge_consecutive_scrolls(flow: WebAgentFlow, **kwargs) -> WebAgentFlow:
    if not flow.steps:
        raise FlowModification(f"No steps in flow: {flow.id}. Title: {flow.title}")

    new_steps = []
    scroll_group = []

    for idx, step in enumerate(flow.steps):
        logger.debug(step.type)
        logger.debug(step.id)
        logger.debug(step.title)
        if step.type == 'scroll':
            scroll_group.append(step.to_dict())
        else:
            if scroll_group:
                keep_step = merge_scroll_group_in_place(scroll_group)
                new_steps.append(keep_step)
                scroll_group = []
            new_steps.append(step.to_dict())

    if scroll_group:
        keep_step = merge_scroll_group_in_place(scroll_group)
        new_steps.append(keep_step)

    flow.to_dict()['steps'] = new_steps
    return flow


def delete_first_launch_app(flow: WebAgentFlow, **kwargs) -> WebAgentFlow:
    force = kwargs.get('force_delete', False)
    note = kwargs.get('extra_note')

    if flow.steps[0].type == 'launchApp':
        delete_step(step=flow.steps[0],
                    force_delete=force,
                    extra_note=note)
        logger.success(f"Current STEP: {json.dumps(flow.steps[0].to_dict(), indent=4, ensure_ascii=False)}")
    return flow


def instruction_level_modify_step_type(flow: WebAgentFlow, **kwargs) -> WebAgentFlow:
    title_type_map = {'向.*滚动':'scroll',
                      '^ANSWER.*': 'answer',
                      '^END.*': 'end'}
    for step in flow.steps:
        for key in title_type_map.keys():
            if re.search(key, step.title.upper()):
                prev_step_type = step.type
                step.type = title_type_map[key]
                logger.warning(f'title: {step.title}: {prev_step_type}->{step.type}')
                break
    return flow
