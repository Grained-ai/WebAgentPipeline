from modules.qc_exceptions import FlowModification
from loguru import logger
from pathlib import Path
from modules.media_utils.video_ops import convert_webm_to_mp4, get_video_duration_ms, merge_scroll_group_in_place
from modules.general_utils import generate_random_id
from modules.webagent_data_utils import WebAgentFlow


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

    for step in flow.steps:
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
