from modules.qc_exceptions import *
from configs.configs import *
from loguru import logger
import glob
import os
from pathlib import Path
from modules.media_utils.video_ops import (convert_webm_to_mp4,
                                           extract_frame_at_timestamp,
                                           extract_frame_webm_at_timestamp)
from modules.media_utils.image_ops import (mark_redo_bbox,
                                           mark_click_position,
                                           crop_browser_from_desktop)
from modules.llm_utils.translate_instruction import translate_step_title
from PIL import Image
import numpy as np
import cv2

from modules.webagent_data_utils import WebAgentStep


def extract_blank_frame(step: WebAgentStep, **kwargs) -> WebAgentStep:
    step_id = step.id
    calibrated_timestamp = step.calibrated_timestamp_ms
    is_negative_timestamp = step.timestamp < 0

    storage_path = Path(kwargs['storage_path'])
    scaled_output = storage_path / 'frames_raw' / f"{step_id}_scaled{'2' if is_negative_timestamp else ''}.jpeg"
    if scaled_output.exists():
        step.screenshot = str(scaled_output.relative_to(storage_path))
        logger.success(f"Found {scaled_output}. Updated.")
        return step
    logger.warning(f"{scaled_output} not exist. Need to extract from video.")
    video_path = storage_path / f"{step.recording_id}.webm"
    mp4_path = storage_path / f"{step.recording_id}.mp4"
    if not video_path.exists():
        raise StepModification(f"Step {step_id} missing video file: {step.recording_id} under {storage_path}")
    if not mp4_path.exists():
        logger.warning(f"Will convert: {video_path}->{mp4_path}")
        convert_webm_to_mp4(video_path, mp4_path)

    raw_output = storage_path / 'frames_raw' / f"{step_id}_raw.jpeg"
    frame = extract_frame_at_timestamp(mp4_path, calibrated_timestamp+50, raw_output)
    if frame is None or not frame.any():
        raise StepException(f"Step {step_id} failed to extract frame from {calibrated_timestamp}")

    if step.to_dict().get("recordingWindowRect"):
        # 完整桌面中截取出浏览器
        frame = crop_browser_from_desktop(frame, step.to_dict()["recordingWindowRect"], step.browser_top_height, step.viewport)["full_browser"]

    target_w = int(step.viewport['width'] * step.device_pixel_ratio)
    orig_h, orig_w = frame.shape[:2]
    scale_ratio = target_w / orig_w
    target_h = int(orig_h * scale_ratio)

    resized = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).resize((target_w, target_h),
                                                                             Image.Resampling.LANCZOS)
    frame = cv2.cvtColor(np.array(resized), cv2.COLOR_RGB2BGR)

    cv2.imwrite(scaled_output, frame.copy())
    step.screenshot = str(scaled_output.relative_to(storage_path))
    return step

def extract_blank_frame_webm(step: WebAgentStep, **kwargs) -> WebAgentStep:
    step_id = step.id
    calibrated_timestamp = step.calibrated_timestamp_ms
    is_negative_timestamp = step.timestamp < 0

    storage_path = Path(kwargs['storage_path'])
    scaled_output = storage_path / 'frames_raw' / f"{step_id}_scaled{'2' if is_negative_timestamp else ''}.jpeg"
    if scaled_output.exists():
        step.screenshot = str(scaled_output.relative_to(storage_path))
        logger.success(f"Found {scaled_output}. Updated.")
        return step
    logger.warning(f"{scaled_output} not exist. Need to extract from video.")
    video_path = storage_path / f"{step.recording_id}.webm"

    if not video_path.exists():
        raise StepModification(f"Step {step_id} missing video file: {step.recording_id} under {storage_path}")

    raw_output = storage_path / 'frames_raw' / f"{step_id}_raw.jpeg"
    frame = extract_frame_webm_at_timestamp(video_path, calibrated_timestamp+50, raw_output)
    if frame is None or not frame.any():
        raise StepException(f"Step {step_id} failed to extract frame from {calibrated_timestamp}")

    target_w = int(step.viewport['width'] * step.device_pixel_ratio)
    orig_h, orig_w = frame.shape[:2]
    scale_ratio = target_w / orig_w
    target_h = int(orig_h * scale_ratio)

    resized = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).resize((target_w, target_h),
                                                                             Image.Resampling.LANCZOS)
    frame = cv2.cvtColor(np.array(resized), cv2.COLOR_RGB2BGR)

    cv2.imwrite(scaled_output, frame.copy())
    step.screenshot = str(scaled_output.relative_to(storage_path))
    return step

# DEPRECATED
def extract_frame(step: WebAgentStep, **kwargs) -> WebAgentStep:
    step_id = step.id

    legacy_image_dir = kwargs.get('legacy_image_dir')
    storage_path = Path(kwargs['storage_path'])

    if legacy_image_dir:
        logger.info(f"Legacy_image_dir detected. Will search for legacy image.")
        saved_image = step.qc_image_used
        if saved_image:
            image_path_parts = saved_image.split('/')[3:]
            file_path = Path(legacy_image_dir) / os.path.join(*image_path_parts)
            if file_path.exists():
                step.screenshot = str(file_path.absolute())
                logger.success(f'Detected legacy image {file_path}. Set to screenshot.')
                return step
            else:
                legacy_image_dir = (Path(legacy_image_dir) / os.path.join(*image_path_parts)).parent
                legacy_image_candidates = glob.glob(f'{step_id}_marked*.jpeg', root_dir=legacy_image_dir)
                for p in legacy_image_candidates:
                    img_path = legacy_image_dir / p
                    if img_path.exists():
                        step.screenshot = str(img_path.absolute())
                        logger.success(f'Detected legacy image {img_path}. Set to screenshot.')
                        return step

        legacy_image_candidates = glob.glob(f'{step_id}_marked*.jpeg', root_dir=Path(legacy_image_dir))
        for p in legacy_image_candidates:
            img_path = Path(legacy_image_dir) / p
            if img_path.exists():
                step.screenshot = str(img_path.absolute())
                logger.success(f'Detected legacy image {img_path}. Set to screenshot.')
                return step

    logger.warning(f'No legacy image found. Need to extract from recording')

    timestamp = step.calibrated_timestamp_ms
    is_negative_timestamp = step.timestamp < 0
    scaled_output = storage_path / 'frames_raw' / f"{step_id}_scaled{'2' if is_negative_timestamp else ''}.jpeg"
    if scaled_output.exists():
        step.screenshot = str(scaled_output.relative_to(storage_path))
        return step

    video_path = storage_path / f"{step.recording_id}.webm"
    mp4_path = storage_path / f"{step.recording_id}.mp4"
    if not video_path.exists():
        raise StepException(f"Step {step_id} missing video file")
    if not mp4_path.exists():
        convert_webm_to_mp4(video_path, mp4_path)

    raw_output = storage_path / 'frames_raw' / f"{step_id}_raw.jpeg"
    frame = extract_frame_at_timestamp(mp4_path, timestamp, raw_output)
    if frame is None or not frame.any():
        raise StepException(f"Step {step_id} failed to extract frame")

    target_w = int(step.viewport['width'] * step.device_pixel_ratio)
    orig_h, orig_w = frame.shape[:2]
    scale_ratio = target_w / orig_w
    target_h = int(orig_h * scale_ratio)

    resized = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).resize((target_w, target_h),
                                                                             Image.Resampling.LANCZOS)
    frame = cv2.cvtColor(np.array(resized), cv2.COLOR_RGB2BGR)

    cv2.imwrite(scaled_output, frame.copy())
    step.screenshot = str(scaled_output.relative_to(storage_path))
    return step


def label_bbox(step: WebAgentStep, **kwargs) -> WebAgentStep:
    storage_path = Path(kwargs['storage_path'])
    if_ignore_missing_exception = kwargs.get("ignore_missing_exception", False)
    if_debug = kwargs.get('if_debug', False)
    if not step.screenshot:
        if not if_ignore_missing_exception:
            raise StepModification("Missing step screenshot. Cannot label.")
        logger.error("Missing step screenshot. Cannot label.")
        return step
    img_path = storage_path / step.screenshot
    if not img_path.exists():  # TODO: Check logic
        step.screenshot = None
        return step
    is_neg = step.timestamp < 0
    output_path = storage_path / 'frames_marked' / f"{step.id}_marked{'2' if is_neg else ''}.jpeg"
    os.makedirs(output_path.parent, exist_ok=True)

    if step.type.lower() not in ['press_enter', 'back', 'cache', 'paste', 'end', 'launchapp']:
        if step.recrop_rect:
            image = Image.open(str(img_path))
            mark_redo_bbox(image, step.recrop_rect)
            logger.debug("Using Annotations.")
            image.save(output_path)

        else:
            frame = cv2.imread(str(img_path))
            frame = mark_click_position(frame, None, None, step.adjusted_rect)
            logger.debug("Using cv2 bbox.")
            cv2.imwrite(output_path, frame)
    else:
        logger.info(f"{step.type}: {step.title} => Set to default screenshot.")
        output_path = img_path

    if not if_debug:
        step.marked_screenshot = str(output_path.relative_to(storage_path))
        storage_relative_path = output_path.relative_to(Path('/var/www/html'))
        step.qc_image_used = "http://3.145.59.104/" + str(storage_relative_path)
    return step

def assign_qc_image_used(step: WebAgentStep, **kwargs)-> WebAgentStep:
    storage_path = Path(kwargs['storage_path'])
    is_neg = step.timestamp < 0
    output_path = storage_path / 'frames_marked' / f"{step.id}_marked{'2' if is_neg else ''}.jpeg"
    storage_relative_path = output_path.relative_to(Path('/var/www/html'))
    step.qc_image_used = "http://3.145.59.104/" + str(storage_relative_path)
    return step

def substitute_step_type(step: WebAgentStep, **kwargs) -> WebAgentStep:
    orig_type = step.type
    orig_title = step.title or ""
    if orig_type == 'type':
        step.title = orig_title.replace('Input', 'Type in') or f"Type in {step.value}"
    elif orig_type == 'paste':
        step.title = f"Type in {step.value}"
        step.type = 'type'
    elif orig_type == 'hover':
        step.title = f"Hover over {step.value}"
    if step.title.upper().startswith('ANSWER'):
        step.type = 'answer'
    return step


def step_title_chinese2english(step: WebAgentStep, **kwargs) -> WebAgentStep:
    orig_title = step.title or ""
    translations = {
        '局部向上滚动': 'Scroll up the boxed part',
        '局部向下滚动': 'Scroll down the boxed part',
        '向上滚动': 'Scroll up the whole screen',
        '向下滚动': 'Scroll down the whole screen'
    }
    if orig_title in translations:
        step.title = translations[orig_title]
    if any('\u4e00' <= ch <= '\u9fff' for ch in step.title):
        input_title = f"{step.type.capitalize()} {step.value or step.title[2:].strip()}"
        input_image = Path(STORAGE_PATH) / step.marked_screenshot if step.marked_screenshot else None
        en = translate_step_title(input_title, input_image)
        step.title = en
    return step


def mark_modify_title(step: WebAgentStep, **kwargs) -> WebAgentStep:
    note = kwargs.get('extra_note')
    step.to_dict().setdefault('fix_methods', []).append(f'Step title modification. Notes: {note}')
    return step


def mark_new_bbox(step: WebAgentStep, **kwargs) -> WebAgentStep:
    note = kwargs.get('extra_note')
    step.to_dict().setdefault('fix_methods', []).append(f'Need to add new bbox. Notes: {note}')
    return step


def delete_step(step: WebAgentStep, **kwargs) -> WebAgentStep:
    note = kwargs.get('extra_note')
    force = kwargs.get('force_delete', False)
    step.to_dict().setdefault('fix_methods', []).append(f'Delete steps. Notes: {note}')
    if force:
        step.deleted = True
        step.title = step.title+'[REMOVED]'
    return step

def visualize_delete_step(step: WebAgentStep, **kwargs) -> WebAgentStep:
    if (step.deleted or step.deleted_by_qc) and 'REMOVED' not in step.title:
        step.title = step.title + '[REMOVED]'
    if step.type == 'launchApp' and '[REMOVED]' not in step.title:
        step.title = ''
        step.deleted = False
        step.qc_image_used = False
    if step.type == 'launchApp' and '[]' in step.title:
        step.title = ''
        step.deleted = False
        step.qc_image_used = False
    return step

def modify_wrong_scroll_rect(step: WebAgentStep, **kwargs) -> WebAgentStep:
    step.rect["top"] = 0

    label_bbox(step, **kwargs)

    return step