import cv2
from PIL import Image
import numpy as np
from modules.media_utils.image_ops import crop_browser_from_desktop
from modules.webagent_data_utils import WebAgentFlow, WebAgentStep
from loguru import logger
from pathlib import Path
from typing import Generator, Callable, Dict, List
import json
from tqdm import tqdm
from datetime import datetime
import math
import re
from modules.linux_utils.linux_utils import init_ssh_client, list_remote_files, backup_existing_images, \
    replace_image_file
from modules.media_utils.video_ops import convert_webm_to_mp4, extract_frame_at_timestamp, extract_frame_at_timestamp_pyav
from modules.step_level_modification import extract_blank_frame
from scripts.archive.hl_bk.regenerate_screenshots import STORAGE_BASE
from scripts.utilities.regenerate_screenshots import regenerate_screenshots_by_step


ROOT_DIR = Path(__file__).parent.parent.parent

JSON_DIR = ROOT_DIR / "jsons"
ALL_JSON_DIR = JSON_DIR / "all_jsons"
ALL_JSON_FILES = list(ALL_JSON_DIR.rglob("*.json"))
SUBMITTED_JSON_DIR = JSON_DIR / "submitted_jsons"
SUBMITTED_JSON_FILES = list(SUBMITTED_JSON_DIR.rglob("*.json"))
MODIFIED_JSON_DIR = JSON_DIR / "modified_jsons"
MODIFIED_JSON_FILES = list(MODIFIED_JSON_DIR.rglob("*.json"))
DELIVERED_JSON_DIR = JSON_DIR / "delivered_jsons"
DELIVERED_JSON_FILES = list(DELIVERED_JSON_DIR.glob("*.json"))

OUTPUT_DIR = ROOT_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
IMG_OUTPUT_DIR = OUTPUT_DIR / "images"
IMG_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TEMP_DIR = ROOT_DIR / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)
VIDEO_DIR = Path(r"C:\Users\11627\Downloads")
VIDEO_FILES = [p for p in VIDEO_DIR.rglob("*.webm") if p.is_file()]

REMOTE_PROJ_DIR = "/var/www/html/"
REMOTE_MARKED_IMG_DIR = "/var/www/html/storage/frames_marked"
REMOTE_RAW_IMG_DIR = "/var/www/html/storage/frames_raw/"
REMOTE_IMG_DIRS = [REMOTE_MARKED_IMG_DIR, REMOTE_RAW_IMG_DIR]

BATCH_SIZE = 30
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")


# ===================== flows转换相关方法 =====================
def json_to_flows(json_files: List[Path] | Generator[Path, None, None] | Path, modify_json_name: bool = True) -> List[WebAgentFlow]:
    """ 从json文件提取转换成 flow 对象列表 """

    def _process(json_file: Path):
        flows_data = json.loads(json_file.read_text(encoding="utf-8"))
        flows = []

        for flow_content in tqdm(flows_data, desc=f"Processing {json_file.name}"):
            flow = WebAgentFlow(flow_content)
            if modify_json_name:
                flow.to_dict()['modified_json_name'] = json_file.name
            flows.append(flow)

        return flows

    if isinstance(json_files, Path):
        return _process(json_files)
    elif isinstance(json_files, List) or isinstance(json_files, Generator):
        all_flows = []

        for json_file in json_files:
            if not isinstance(json_file, Path):
                raise TypeError(f"Each file must be a Path object, got {type(json_file)}")

            all_flows.extend(_process(json_file))

        return all_flows
    else:
        raise TypeError(f"json_file must be Path or list[Path], got {type(json_files)}")

def json_to_flows_dict(json_files: List[Path] | Generator[Path, None, None] | Path, modify_json_name: bool = True) -> Dict[str, List[WebAgentFlow]]:
    """ 从json文件提取转换 flow 字典列表 """
    if isinstance(json_files, Path):
        json_files = [json_files]

    return {json_file.stem: json_to_flows(json_file, modify_json_name=modify_json_name) for json_file in json_files}

def flows_to_excel(flows: List[WebAgentFlow],
                   batch_keyword: str,
                   columns: List[str] = ["instruction", "instruction_id", "json_name", "url"],
                   batch_size: int = BATCH_SIZE):
    import pandas as pd

    def _create_excel_from_flows(flows: List[WebAgentFlow], filename: str) -> str:
        """创建Excel文件并返回文件路径"""
        file_dir = OUTPUT_DIR / f"{batch_keyword}_{TIMESTAMP}"
        file_dir.mkdir(parents=True, exist_ok=True)
        file_path = file_dir / filename

        data_rows = []

        for flow in flows:
            data = []
            for column in columns:
                if column == "instruction_id":
                    data.append(flow.id)
                elif column == "instruction":
                    data.append(flow.title)
                elif column == "json_name":
                    data.append(flow.to_dict().get("modified_json_name"))
                elif column == "annotator":
                    json_name = flow.to_dict().get("modified_json_name")
                    json_stem = json_name.replace(".json", "")
                    if "[" in json_stem:
                        annotator = re.search(r'\[([^\]]+)\]', json_stem).group(1)
                    else:
                        annotator = json_stem.split("_")[0]
                    data.append(annotator)
                elif column in ["host", "website", "web", "url"]:
                    data.append(get_value_from_steps(flow, "host"))
                elif column == "recording_id":
                    data.append(get_value_from_steps(flow, "recordingId"))
                else:
                    data.append(flow.to_dict().get(column))
            # logger.debug(f"{column}: {data}")

            data_rows.append(data)

        df = pd.DataFrame(data_rows, columns=columns)
        df.to_excel(file_path, index=False)
        return str(file_path)

    # flow_dicts = [flow.to_dict() for flow in flows]

    # 如果batch_size为0，不切割
    if batch_size == 0:
        filename = f"{batch_keyword}_flows_{TIMESTAMP}.xlsx"
        file_path = _create_excel_from_flows(flows, filename)
        print(f"Excel文件已创建: {file_path}")
        return [file_path]

    # 计算需要切割的批次数
    total_flows = len(flows)
    num_batches = math.ceil(total_flows / batch_size)
    created_files = []

    # 切割并创建多个Excel文件
    for batch_index in range(num_batches):
        start_idx = batch_index * batch_size
        end_idx = min(start_idx + batch_size, total_flows)
        batch_flows = flows[start_idx:end_idx]

        filename = f"{batch_keyword}_flows_batch_{batch_index + 1:03d}_{TIMESTAMP}.xlsx"
        file_path = _create_excel_from_flows(batch_flows, filename)
        created_files.append(file_path)
        print(f"批次 {batch_index + 1}/{num_batches} Excel文件已创建: {file_path}")

    return created_files

def flows_to_json(flows: List[WebAgentFlow], batch_keyword: str, batch_size: int = BATCH_SIZE):
    # if not dicts:
    #     logger.warning("No data to save")
    #     return []

    def _create_json_from_flows(flows: List[WebAgentFlow], filename: str) -> Path:
        """创建JSON文件并返回文件路径"""
        file_dir = OUTPUT_DIR / f"{batch_keyword}_{TIMESTAMP}"
        file_dir.mkdir(parents=True, exist_ok=True)
        file_path = file_dir / filename

        flow_dicts = [flow.to_dict() for flow in flows]

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(flow_dicts, f, ensure_ascii=False, indent=4)

        return file_path

    # 如果batch_size为0，不切割
    if batch_size == 0:
        filename = f"{batch_keyword}_flows_{TIMESTAMP}.json"
        file_path = _create_json_from_flows(flows, filename)
        logger.success(f"Saved {len(flows)} flows to {file_path.name}")
        return [file_path]

    # 计算需要切割的批次数
    total_batches = math.ceil(len(flows) / batch_size)
    logger.info(f"Creating {total_batches} batch files with up to {batch_size} flows each")
    created_files = []

    # 切割并创建多个JSON文件
    for batch_index in range(total_batches):
        start_idx = batch_index * batch_size
        end_idx = min(start_idx + batch_size, len(flows))
        batch_flows = flows[start_idx:end_idx]

        filename = f"{batch_keyword}_flows_batch_{batch_index + 1:03d}_{TIMESTAMP}.json"
        file_path = _create_json_from_flows(batch_flows, filename)
        created_files.append(file_path)

        logger.success(f"Saved batch {batch_index + 1} with {len(batch_flows)} flows to {file_path.name}")
        logger.info(f"Batch {batch_index + 1}: {len(batch_flows)} flows")

    logger.success(f"All {total_batches} batch files created successfully")
    return created_files


# ===================== flows清洗相关方法 =====================
def subtract_flows(origin_flows: List[WebAgentFlow], target_flows: List[WebAgentFlow]) -> List[WebAgentFlow]:
    target_ids = {flow.title for flow in target_flows}

    return [flow for flow in origin_flows if flow.title not in target_ids]

def dedup_flows_by_id(flows: List[WebAgentFlow]) -> List[WebAgentFlow]:
    # id_set = set()
    # dedup_flows = []
    #
    # for flow in flows:
    #     if flow.id not in id_set:
    #         id_set.add(flow.id)
    #         dedup_flows.append(flow)
    #
    # # return dedup_flows

    return list({flow.id: flow for flow in flows}.values())

def dedup_flows_by_title(flows: List[WebAgentFlow]) -> List[WebAgentFlow]:
    # title_set = set()
    # dedup_flows = []
    #
    # for flow in flows:
    #     if flow.title not in title_set:
    #         title_set.add(flow.title)
    #         dedup_flows.append(flow)
    #
    # return dedup_flows

    return list({flow.title: flow for flow in flows}.values())

def extract_non_rect_flows(flows: List[WebAgentFlow], certain_steps_only: bool = False) -> List[WebAgentFlow]:
    non_rect_flows = []

    for flow in flows:
        non_rect_steps = []

        for step in flow.steps:
            if (step.type.lower() not in ['press_enter', 'back', 'cache', 'paste', 'end', 'launchapp']
                    and step.title.lower() not in ['end']):
                if not step.adjusted_rect and not step.recrop_rect:
                    if not certain_steps_only:
                        non_rect_flows.append(flow)
                        break

                    non_rect_steps.append(step)

        if certain_steps_only and non_rect_steps:
            flow.to_dict()["steps"] = [step.to_dict() for step in non_rect_steps]
            flow._steps = non_rect_steps
            non_rect_flows.append(flow)

    return non_rect_flows

def extract_marked_flows_without_rect(flows: List[WebAgentFlow], certain_steps_only: bool = False) -> List[WebAgentFlow]:
    """ 似乎跟上面的代码是一回事，区别在于这个方法先判断有没有marked过（imgSave）再判断有没有rect """
    marked_flows_without_rect = []

    for flow in flows:
        marked_steps_without_rect = []

        for step in flow.steps:
            if step.to_dict().get("imgSave") and not step.rect and not step.recrop_rect:
                if not certain_steps_only:
                    marked_flows_without_rect.append(flow)
                    break

                marked_steps_without_rect.append(step)

        if certain_steps_only and marked_steps_without_rect:
            flow.to_dict()["steps"] = [step.to_dict() for step in marked_steps_without_rect]
            flow._steps = marked_steps_without_rect
            marked_flows_without_rect.append(flow)

    return marked_flows_without_rect

def extract_redo_flows(flows: List[WebAgentFlow]) -> List[WebAgentFlow]:
    redo_flows = []

    for flow in flows:
        for step in flow.steps:
            logger.debug(f"Step {step.id}: {step.title}")
            if "redo" in step.title.lower():
                redo_flows.append(flow)
                break

    return redo_flows

def extract_non_redo_flows(flows: List[WebAgentFlow]) -> List[WebAgentFlow]:
    non_redo_flows = []

    for flow in flows:
        for step in flow.steps:
            if "redo" not in step.title.lower():
                non_redo_flows.append(flow)
                break

    return non_redo_flows

def extract_non_img_flows(flows: List[WebAgentFlow], certain_steps_only: bool = False) -> List[WebAgentFlow]:
    non_img_flows = []

    ssh_client = init_ssh_client()

    remote_imgs = list_remote_files(ssh_client, REMOTE_RAW_IMG_DIR)
    
    exist_ids = set()
    for remote_img in remote_imgs:
        if remote_img:  # 确保文件名不为空
            stem = Path(remote_img).stem
            exist_id = stem.rsplit("_", 1)[0]
            exist_ids.add(exist_id)

    for flow in flows:
        non_img_steps = []

        for step in flow.steps:
            if step.type not in ['cache', 'paste', 'launchApp'] and not step.deleted and not step.deleted_by_qc:
                if step.id not in exist_ids:
                    if not certain_steps_only:
                        non_img_flows.append(flow)
                        break

                    non_img_steps.append(step)

        if certain_steps_only and non_img_steps:
            flow.to_dict()["steps"] = [step.to_dict() for step in non_img_steps]
            flow._steps = non_img_steps
            non_img_flows.append(flow)

    return non_img_flows

def extract_is_remake_flows(flows: List[WebAgentFlow], certain_steps_only: bool = False) -> List[WebAgentFlow]:
    is_remake_flows = []
    appended_flow_instructions = set()

    for flow in flows:
        if flow.title not in appended_flow_instructions:
            is_remake_steps = []

            for step in flow.steps:
                if step.is_remake:
                    if not certain_steps_only:
                        is_remake_flows.append(flow)
                        break

                    is_remake_steps.append(step)

            if certain_steps_only and is_remake_steps:
                flow.to_dict()["steps"] = [step.to_dict() for step in is_remake_steps]
                flow._steps = is_remake_steps
                is_remake_flows.append(flow)
                appended_flow_instructions.add(flow.title)

    return is_remake_flows

def extract_select_or_drag_steps(flows: List[WebAgentFlow]) -> List[dict]:
    select_or_drag_flows = []

    for flow in flows:
        select_or_drag_steps = []

        for step in flow.steps:
            if step.type in ["select", "drag"]:
                logger.debug(f"Found {step.type} step {step.to_dict()}")
                select_or_drag_steps.append(step)

        if select_or_drag_steps:
            flow.to_dict()["steps"] = [step.to_dict() for step in select_or_drag_steps]
            select_or_drag_flows.append(flow)

    return select_or_drag_flows

def find_unsubmitted_flows_by_title(all_flows: List[WebAgentFlow], submitted_flows: List[WebAgentFlow]) -> List[WebAgentFlow]:
    submitted_flow_instructions = [flow.title for flow in submitted_flows]

    return [flow for flow in all_flows if flow.title not in submitted_flow_instructions]

def find_unsubmitted_flows_by_id(all_flows: List[WebAgentFlow], submitted_flows: List[WebAgentFlow]) -> List[WebAgentFlow]:
    submitted_flow_ids = [flow.id for flow in submitted_flows]

    return [flow for flow in all_flows if flow.id not in submitted_flow_ids]

def find_unsubmitted_modified_flows(unsubmitted_flows: List[WebAgentFlow], modified_flows: List[WebAgentFlow]) -> List[WebAgentFlow]:
    unsubmitted_flow_instructions = [flow.title for flow in unsubmitted_flows]

    return [modified_flow for modified_flow in modified_flows if modified_flow.title in unsubmitted_flow_instructions]

def sort_flows_by_host(flow_dicts: List[dict]) -> List[dict]:
    return sorted(flow_dicts, key=lambda x: next(
        (step['host'] for step in x.get('steps', []) if step.get('host')),
        ''  # 默认值，如果没有找到
    ))


# ===================== flows批量截图相关方法 =====================
def find_video_file(recording_id: str) -> Path:
    for video_file in VIDEO_FILES:
        if recording_id in video_file.name:
            return video_file
    return None

def extract_single_frame_from_flows(flows: list[WebAgentFlow], video_dir: Path) -> list[Path]:
    generated_images = []

    for flow in flows:
        # if flow.id not in ["lXWZIBmjtPSmqEZ0iMpFK", "eU3Js9ITplzLn-jz11Nii", "noQyaHM2Ne5aNIdECET7K"]:
        #     continue

        for idx, step in enumerate(flow.steps):
            # if idx != 2:
            #     continue

            if not step.recording_id:
                continue

            flow.steps[idx] = extract_blank_frame(step, storage_path=IMG_OUTPUT_DIR, video_dir=video_dir)
            generated_images.extend(list(IMG_OUTPUT_DIR.rglob(f"{step.id}*.jpeg")))

    return generated_images

def extract_candidate_frames_from_flows(flows: list[WebAgentFlow]) -> list[Path]:
    generated_images = []

    for flow in flows:
        for idx, step in enumerate(flow.steps):
            if not step.to_dict().get("isremake"):
                continue

            generated_images_per_step = []

            webm_video_path = find_video_file(step.recording_id)
            if webm_video_path is None:
                logger.error(f"Could not find video file for recording_id: {step.recording_id}")
                return False

            # Webm直接截取给定Timestamp作为candidates的第0张
            blank_frame_webm_file = STORAGE_BASE / f"{step.id}_candidate_0_{step.calibrated_timestamp_ms}.jpeg"
            if not blank_frame_webm_file.exists():
                blank_frame_webm = extract_frame_at_timestamp_pyav(
                    webm_video_path,
                    step.calibrated_timestamp_ms,
                    blank_frame_webm_file,
                )
                if step.to_dict().get("recordingWindowRect"):
                    # 完整桌面中截取出浏览器
                    blank_frame_webm = crop_browser_from_desktop(blank_frame_webm, step.to_dict()["recordingWindowRect"], step.browser_top_height, step.viewport)["full_browser"]

                target_w = int(step.viewport['width'] * step.device_pixel_ratio)
                orig_h, orig_w = blank_frame_webm.shape[:2]
                scale_ratio = target_w / orig_w
                target_h = int(orig_h * scale_ratio)

                resized = Image.fromarray(cv2.cvtColor(blank_frame_webm, cv2.COLOR_BGR2RGB)).resize((target_w, target_h), Image.Resampling.LANCZOS)
                frame = cv2.cvtColor(np.array(resized), cv2.COLOR_RGB2BGR)

                cv2.imwrite(str(blank_frame_webm_file), frame.copy())
            if blank_frame_webm_file.exists():
                generated_images_per_step.append(blank_frame_webm_file)

            # MP4截取candidates
            mp4_video_path = webm_video_path.parent / f"{step.recording_id}.mp4"
            if not mp4_video_path.exists():
                logger.info(f"Converting {webm_video_path} to {mp4_video_path}")
                convert_webm_to_mp4(webm_video_path, mp4_video_path)

                if not mp4_video_path.exists():
                    logger.error(f"MP4 conversion failed for {step.id}")
                    return False

            logger.info(f"Processing step {step.id} with video {mp4_video_path}")
            generated_images_per_step.extend(regenerate_screenshots_by_step(step, mp4_video_path))

            if generated_images_per_step:
                # 将生成的截图路径存储到step的candidates字段
                step.to_dict()["screenshot_options"] = ["http://3.145.59.104/pickimgjson/hl/" + generated_image.name for generated_image in generated_images_per_step]

                logger.success(f"Successfully processed step {step.id}")

            generated_images.extend(generated_images_per_step)

    return generated_images

def copy_pick_img_from_flows(flows: List[WebAgentFlow]) -> list[Path]:
    # 1. 收集step.ids 和 pickimgs
    # 2. 备份 frames_raw/{step.id}_scaled*.jpeg -> frames_raw/{step.id}_scaled*_bak.jpeg
    # 3. pickimgs 重命名到 frames_raw/{step.id}_scaled.jpeg

    # pick_imgs = [step.to_dict().get("pickimg") for flow in flows for step in flow.steps]
    pick_imgs = []
    step_ids = []
    is_negative_timestamps = []
    for flow in flows:
        for step in flow.steps:
            if step.to_dict().get("pickimg"):
                pick_imgs.append(step.to_dict().get("pickimg"))
                step_ids.append(step.id)
                is_negative_timestamps.append(step.timestamp < 0)
            else:
                logger.critical(f"⌈{flow.title}⌋ - ⌈{step.title}⌋ no pickimg!!!")

    try:
        ssh_client = init_ssh_client()

        for step_id, pick_img, is_negative_timestamp in zip(step_ids, pick_imgs, is_negative_timestamps):
            backup_existing_images(ssh_client, REMOTE_RAW_IMG_DIR, step_id + "_scaled")

            pick_img_file = "/".join(pick_img.split("/")[-3:])
            source_img_file = REMOTE_PROJ_DIR + pick_img_file
            dst_img_file = REMOTE_RAW_IMG_DIR + f"{step_id}_scaled{'2' if is_negative_timestamp else ''}.jpeg"

            replace_image_file(ssh_client, source_img_file, dst_img_file)
    finally:
        ssh_client.close()


# ===================== 其它方法 =====================
def get_value_from_steps(flow: WebAgentFlow, key: str) -> str | None:
    """ 从一个 instruction 中所有step获取第一个不为空的值（例如提取url、recordingId）"""
    for step in flow.steps:
        if not step.to_dict().get(key):
            continue

        return step.to_dict().get(key)

    return None

# def extract_and_export_certain_flows(
#         json_files: List[Path] | Generator[Path, None, None] | Path,
#         modify_json_name: bool,
#         extractor: Callable[[List[WebAgentFlow]], List[WebAgentFlow]],
#         experter: Callable[[List[WebAgentFlow]], List],
#         batch_size: int,
#         processor: Callable[[List[WebAgentFlow]], List],):
#     all_flows = json_to_flows(json_files)
#
#     certain_flows = extractor(all_flows, )
