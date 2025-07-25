from loguru import logger
from modules.webagent_data_utils import WebAgentFlow, WebAgentStep
from modules.step_level_modification import extract_blank_frame, label_bbox, extract_frame_at_timestamp
from modules.media_utils.image_ops import mark_click_position, crop_browser_from_desktop
from pathlib import Path
import json
import cv2
from PIL import Image
import numpy as np
from modules.media_utils.video_ops import get_video_duration_ms


STORAGE_BASE = Path(r"C:\Users\dehan\Desktop\WedAgentPipeline_hl\fix_wrong_frame")

# with open('/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/fix_wrong_frame/fix_content.json', 'r') as f:
#     data = json.load(f)
#
# flow_ins = WebAgentFlow(flow_dict=data)
# id = 'VLC1ZDVpE83UAvuqEmQdx'
# for idx, step in enumerate(flow_ins.steps):
#     if step.id == id:
#         duration = (flow_ins.steps[idx + 1].timestamp - step.timestamp) // 15
#         for candi, timestamp in enumerate(range(step.timestamp, flow_ins.steps[idx + 1].timestamp, duration)):
#             image_path = STORAGE_BASE / "debug.jpeg"
#             marked_image_path = STORAGE_BASE / f"marked_debug_{candi}.jpeg"
#             extract_frame_at_timestamp(
#                 STORAGE_BASE / str(step.recording_id + '.mp4'),
#                 timestamp_ms=step.timestamp + duration,
#                 output_image_path=image_path)
#             frame = cv2.imread(str(image_path))
#             # frame2 = mark_click_position(frame, None, None, step.adjusted_rect)
#             # cv2.imwrite(marked_image_path, frame2)

# def regenerate_screenshots_by_step(step: WebAgentStep): # -> list[Path]:
#     steps = step.parent_flow.steps
#     step_idx = steps.index(step)
#
#     duration = (steps[step_idx - 1].timestamp - step.timestamp) // 15
#     for candi, timestamp in enumerate(range(step.timestamp, steps[step_idx - 1].timestamp, duration)):
#         # image_path = STORAGE_BASE / "debug.jpeg"
#         marked_image_path = STORAGE_BASE / f"{step.id}_marked_debug_{candi}.jpeg"
#         extract_frame_at_timestamp(
#             STORAGE_BASE / str(step.recording_id + '.mp4'),
#             timestamp_ms=step.timestamp + duration,
#             output_image_path=marked_image_path)
#         # frame = cv2.imread(str(image_path))
#         # frame2 = mark_click_position(frame, None, None, step.adjusted_rect)
#         # cv2.imwrite(marked_image_path, frame2)
#
#     # return l


def regenerate_screenshots_by_step(step: WebAgentStep, video_path: Path) -> list[Path]:
    """
    为指定步骤重新生成截图

    Args:
        step: WebAgentStep对象
        video_path: 视频文件路径

    Returns:
        list[Path]: 生成的图片路径列表
    """
    steps = step.parent_flow.steps
    step_idx = steps.index(step)

    generated_images = []

    if step_idx == 0:
        start_timestamp = step.calibrated_timestamp_ms // 2
        end_timestamp = (steps[step_idx + 1].calibrated_timestamp_ms + step.calibrated_timestamp_ms) // 2
    elif step_idx == len(steps) - 1:  # 检查是否为最后一个 step
        video_duration = get_video_duration_ms(video_path)
        if step.calibrated_timestamp_ms == video_duration:
            return [Path(step.screenshot)]
        else:
            start_timestamp = (steps[step_idx - 1].calibrated_timestamp_ms + step.calibrated_timestamp_ms) // 2
            end_timestamp = video_duration
            # duration = video_duration - step.calibrated_timestamp_ms
    else:
        start_timestamp = (steps[step_idx - 1].calibrated_timestamp_ms + step.calibrated_timestamp_ms) // 2
        end_timestamp = (steps[step_idx + 1].calibrated_timestamp_ms + step.calibrated_timestamp_ms) // 2
    duration = (end_timestamp - start_timestamp) // 20

    logger.debug(f"Step {step.parent_flow.id} {step.id} Calibrated Timestamp {step.calibrated_timestamp_ms}")
    # logger.debug(f"Will Process {step.id}, {start_timestamp}, {end_timestamp}, {duration}")
    logger.debug(
        f"Will Process {step.parent_flow.id} {step.id}, {start_timestamp}, {end_timestamp}, {[timestamp for timestamp in range(start_timestamp, end_timestamp, duration)]}")
    for candi, timestamp in enumerate(range(start_timestamp, end_timestamp, duration)):
        # logger.debug(f"Processing {step.id} {candi} {timestamp}")
        regene_image_path = STORAGE_BASE / f"{step.id}_candidate_{candi + 1}_{timestamp}.jpeg"
        if regene_image_path.exists():
            generated_images.append(regene_image_path)
            continue

        try:
            frame = extract_frame_at_timestamp(
                video_path,
                timestamp_ms=timestamp,
                output_image_path=regene_image_path
            )

            if step.to_dict().get("recordingWindowRect"):
                # 完整桌面中截取出浏览器
                frame = crop_browser_from_desktop(frame, step.to_dict()["recordingWindowRect"], step.browser_top_height, step.viewport)["full_browser"]

            target_w = int(step.viewport['width'] * step.device_pixel_ratio)
            orig_h, orig_w = frame.shape[:2]
            scale_ratio = target_w / orig_w
            target_h = int(orig_h * scale_ratio)

            resized = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).resize((target_w, target_h), Image.Resampling.LANCZOS)
            frame = cv2.cvtColor(np.array(resized), cv2.COLOR_RGB2BGR)

            cv2.imwrite(str(regene_image_path), frame.copy())

            # 如果成功生成图片，添加到列表中
            if regene_image_path.exists():
                generated_images.append(regene_image_path)

        except Exception as e:
            logger.error(f"Error generating screenshot for step {step.id} at timestamp {timestamp}: {e}")
            continue

    return generated_images