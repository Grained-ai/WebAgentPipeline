from modules.webagent_data_utils import WebAgentFlow, WebAgentStep
from loguru import logger
from pathlib import Path
from typing import Generator, Callable, Dict
import json
from tqdm import tqdm
import traceback
from datetime import datetime
import math
import re


ROOT_DIR = Path(__file__).parent.parent.parent
JSON_DIR = ROOT_DIR / "jsons"
ALL_JSON_DIR = JSON_DIR / "all_jsons"
ALL_JSON_FILES = list(ALL_JSON_DIR.rglob("*.json"))
SUBMITTED_JSON_DIR = JSON_DIR / "submitted_jsons"  # 修正拼写
SUBMITTED_JSON_FILES = list(SUBMITTED_JSON_DIR.rglob("*.json"))
MODIFIED_JSON_DIR = JSON_DIR / "modified_jsons"
MODIFIED_JSON_FILES = list(MODIFIED_JSON_DIR.rglob("*.json"))
OUTPUT_DIR = ROOT_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
IMG_OUTPUT_DIR = OUTPUT_DIR / "images"
IMG_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TEMP_DIR = ROOT_DIR / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)
VIDEO_DIR = Path(r"C:\Users\11627\Downloads")
VIDEO_FILES = [p for p in VIDEO_DIR.rglob("*.webm") if p.is_file()]

BATCH_SIZE = 30

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")


# ===================== 数据转换相关方法 =====================
def json_to_flows(json_files: list[Path] | Generator[Path, None, None] | Path, modify_json_name: bool = True) -> list[WebAgentFlow]:
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
    elif isinstance(json_files, list) or isinstance(json_files, Generator):
        all_flows = []

        for json_file in json_files:
            if not isinstance(json_file, Path):
                raise TypeError(f"Each file must be a Path object, got {type(json_file)}")

            all_flows.extend(_process(json_file))

        return all_flows
    else:
        raise TypeError(f"json_file must be Path or list[Path], got {type(json_files)}")

def json_to_flows_dict(json_files: list[Path] | Generator[Path, None, None] | Path, modify_json_name: bool = True) -> Dict[str, list[WebAgentFlow]]:
    if isinstance(json_files, Path):
        json_files = [json_files]

    return {json_file.stem: json_to_flows(json_file, modify_json_name=modify_json_name) for json_file in json_files}

def subtract_flows(origin_flows: list[WebAgentFlow], target_flows: list[WebAgentFlow]) -> list[WebAgentFlow]:
    target_ids = {flow.title for flow in target_flows}

    return [flow for flow in origin_flows if flow.title not in target_ids]

def dedup_flows_by_id(flows: list[WebAgentFlow]) -> list[WebAgentFlow]:
    id_set = set()
    dedup_flows = []

    for flow in flows:
        if flow.id not in id_set:
            id_set.add(flow.id)
            dedup_flows.append(flow)

    return dedup_flows

def dedup_flows_by_title(flows: list[WebAgentFlow]) -> list[WebAgentFlow]:
    title_set = set()
    dedup_flows = []

    for flow in flows:
        if flow.title not in title_set:
            title_set.add(flow.title)
            dedup_flows.append(flow)

    return dedup_flows

# ===================== 数据清洗相关方法 =====================
def extract_non_rect_flows(flows: list[WebAgentFlow]) -> list[WebAgentFlow]:
    non_rect_flows = []

    for flow in flows:
        for step in flow.steps:
            if step.type.lower() not in ['press_enter', 'back', 'cache', 'paste', 'end', 'launchapp'] and step.title.lower() not in [
                'end']:
                if not step.is_remake and not step.adjusted_rect and not step.recrop_rect:
                    non_rect_flows.append(flow)
                    break

    return non_rect_flows

def extract_redo_flows(flows: list[WebAgentFlow]) -> list[WebAgentFlow]:
    redo_flows = []

    for flow in flows:
        for step in flow.steps:
            logger.debug(f"Step {step.id}: {step.title}")
            if "redo" in step.title.lower():
                redo_flows.append(flow)
                break

    return redo_flows

def extract_non_redo_flows(flows: list[WebAgentFlow]) -> list[WebAgentFlow]:
    non_redo_flows = []

    for flow in flows:
        for step in flow.steps:
            if "redo" not in step.title.lower():
                non_redo_flows.append(flow)
                break

    return non_redo_flows

# def extract_is_remake_flows(json_files: list[Path]) -> list[WebAgentFlow]:
#     is_remake_flows = []
#     has_remake_steps = False
#     appended_flow_instructions = set()
#
#     for json_file in json_files:
#         try:
#             flows_data = json.loads(json_file.read_text(encoding="utf-8"))
#
#             for flow_content in tqdm(flows_data, desc=f"Processing {json_file.name}"):
#                 flow = WebAgentFlow(flow_content)
#
#                 if flow.title not in appended_flow_instructions:
#                     for step_dict in flow.steps:
#                         step = step_dict if isinstance(step_dict, WebAgentStep) else WebAgentStep(step_dict, parent_flow=flow)
#
#                         if step.is_remake:
#                             has_remake_steps = True
#                             break
#
#                     if has_remake_steps:
#                         flow.to_dict()['modified_json_name'] = json_file.name
#                         is_remake_flows.append(flow)
#                         appended_flow_instructions.add(flow.title)
#
#         except Exception as e:
#             logger.error(f"Error processing {json_file.name}: {e}")
#             logger.debug(traceback.format_exc())
#             continue
#
#     return is_remake_flows

def find_unsubmitted_flows(all_flows: list[WebAgentFlow], submitted_flows: list[WebAgentFlow]) -> list[WebAgentFlow]:
    submitted_flow_instructions = [flow.title for flow in submitted_flows]
    unsubmitted_flows = []

    for flow in all_flows:
        if flow.title not in submitted_flow_instructions:
            unsubmitted_flows.append(flow)

    return unsubmitted_flows

def find_unsubmitted_flows_by_id(all_flows: list[WebAgentFlow], submitted_flows: list[WebAgentFlow]) -> list[WebAgentFlow]:
    submitted_flow_ids = [flow.id for flow in submitted_flows]
    unsubmitted_flows = []

    for flow in all_flows:
        if flow.id not in submitted_flow_ids:
            unsubmitted_flows.append(flow)

    return unsubmitted_flows

def find_unsubmitted_modified_flows(unsubmitted_flows: list[WebAgentFlow], modified_flows: list[WebAgentFlow]) -> list[WebAgentFlow]:
    unsubmitted_flow_instructions = [flow.title for flow in unsubmitted_flows]
    unsubmitted_modified_flows = []

    for modified_flow in modified_flows:
        if modified_flow.title in unsubmitted_flow_instructions:
            unsubmitted_modified_flows.append(modified_flow)

    return unsubmitted_modified_flows

def extract_is_remake_steps(flows: list[WebAgentFlow]) -> list[dict]:
    is_remake_flow_dicts = []

    for flow in flows:
        remake_steps = []

        # 收集所有remake步骤，不要break
        for step in flow.steps:
            # logger.debug(f"Found remake step {step.to_dict()}")
            if step.is_remake:
                # logger.debug(f"Found remake step {step.to_dict()}")
                logger.info(f"Found remake step {step.id}")
                remake_steps.append(step)

        # 如果有remake步骤，创建flow字典
        if remake_steps:
            is_remake_flow_dict = flow.to_dict().copy()
            is_remake_flow_dict["steps"] = [step.to_dict() for step in remake_steps]
            # is_remake_flow_dict["steps"] = [step.to_dict() for step in remake_steps if step.type not in ["select", "drag"]]
            is_remake_flow_dicts.append(is_remake_flow_dict)

    return is_remake_flow_dicts


def extract_select_or_drag_steps(flows: list[WebAgentFlow]) -> list[dict]:
    has_select_or_drag_dicts = []

    for flow in flows:
        select_or_drag_steps = []

        for step in flow.steps:
            if step.type in ["select", "drag"]:
                logger.debug(f"Found {step.type} step {step.to_dict()}")
                select_or_drag_steps.append(step)

        if select_or_drag_steps:
            select_or_drag_flow_dict = flow.to_dict().copy()
            select_or_drag_flow_dict["steps"] = [step.to_dict() for step in select_or_drag_steps]
            has_select_or_drag_dicts.append(select_or_drag_flow_dict)

    return has_select_or_drag_dicts

def sort_by_host(flow_dicts: list[dict]) -> list[dict]:
    return sorted(flow_dicts, key=lambda x: next(
    (step['host'] for step in x.get('steps', []) if step.get('host')),
    ''  # 默认值，如果没有找到
))

def find_video_file(recording_id: str) -> Path:
    for video_file in VIDEO_FILES:
        if recording_id in video_file.name:
            return video_file
    return None

def extract_browser_screenshots(flows: list[WebAgentFlow], video_dir: Path):
    from modules.step_level_modification import extract_blank_frame_webm
    from modules.media_utils.video_ops import convert_webm_to_mp4, extract_frame_at_timestamp
    from modules.linux_utils.linux_utils import upload_images_to_server

    for flow in flows:
        for step in flow.steps:
            # if not step.recording_id:
            #     continue

            # if not step.is_remake:
            #     continue

            if step.id not in ['dvx3n-xYQK7Xq3wLR0ORL', '9Q83IwslTlQTBGsRloWZI']:
                continue

            try:
                from modules.step_level_modification import extract_blank_frame
                extract_blank_frame_webm(step, storage_path=IMG_OUTPUT_DIR, video_dir=find_video_file(step.recording_id).parent)
            except Exception as e:
                logger.error(f"Error processing step {step.id}: {e}")
                logger.debug(traceback.format_exc())
                continue

# def extract_screenshots_and_upload(flows: list[WebAgentFlow]):
#     from modules.media_utils.video_ops import convert_webm_to_mp4, extract_frame_at_timestamp
#     from linux_utils import upload_images_to_server
#
#     for flow in flows:
#         for step in flow.steps:
#             webm_video_path = find_video_file(step.recording_id)
#
#             if webm_video_path is None:
#                 logger.error(f"Could not find video file for recording_id: {step.recording_id}")
#                 return False
#
#             mp4_video_path = TEMP_DIR / f"{step.id}.mp4"
#
#             try:
#                 # 检查MP4文件是否存在，不存在才进行转换
#                 if not mp4_video_path.exists():
#                     logger.info(f"Converting {webm_video_path} to {mp4_video_path}")
#                     convert_webm_to_mp4(webm_video_path, mp4_video_path)
#
#                     if not mp4_video_path.exists():
#                         logger.error(f"MP4 conversion failed for {step.recording_id}")
#                         return False
#
#                 logger.info(f"Processing step {step.id} with video {mp4_video_path}")
#
#                 # 使用带重试机制的截图生成
#                 generated_image = extract_frame_at_timestamp(
#                     mp4_video_path,
#                     step.calibrated_timestamp_ms,
#                     IMG_OUTPUT_DIR / f"{step.id}.jpeg",
#                 )
#
#                 if generated_image:
#                     logger.debug(f"Generated {len(generated_image)} images for step {step.id}")
#
#                     # 上传图片到服务器
#                     uploaded_image_names = upload_images_to_server([generated_image])
#
#                     # 将生成的截图路径存储到step的candidates字段
#                     step.to_dict()["screenshot_options"] = ["http://3.145.59.104/pickimgjson/hl/" + name for name in
#                                                             uploaded_image_names]
#
            #         logger.success(f"Successfully processed step {step.id}")
            #         return True
            #     else:
            #         logger.warning(f"No screenshots generated for step {step.id} after all retry attempts")
            #         return False
            #
            # except Exception as e:
            #     logger.error(f"Error processing step {step.id}: {e}")
            #     logger.debug(traceback.format_exc())
            #     return False

def extract_screenshots_and_upload(flows: list[WebAgentFlow]):
    from modules.media_utils.video_ops import convert_webm_to_mp4, extract_frame_at_timestamp
    from modules.linux_utils.linux_utils import upload_images_to_server

    for flow in flows:
        for step in flow.steps:
            webm_video_path = find_video_file(step.recording_id)

            if webm_video_path is None:
                logger.error(f"Could not find video file for recording_id: {step.recording_id}")
                return False

            mp4_video_path = TEMP_DIR / f"{step.id}.mp4"

            try:
                # 检查MP4文件是否存在，不存在才进行转换
                if not mp4_video_path.exists():
                    logger.info(f"Converting {webm_video_path} to {mp4_video_path}")
                    convert_webm_to_mp4(webm_video_path, mp4_video_path)

                    if not mp4_video_path.exists():
                        logger.error(f"MP4 conversion failed for {step.recording_id}")
                        return False

                logger.info(f"Processing step {step.id} with video {mp4_video_path}")

                # 使用带重试机制的截图生成
                generated_image = extract_frame_at_timestamp(
                    mp4_video_path,
                    step.calibrated_timestamp_ms,
                    IMG_OUTPUT_DIR / f"{step.id}.jpeg",
                )

                if generated_image:
                    logger.debug(f"Generated {len(generated_image)} images for step {step.id}")

                    # 上传图片到服务器
                    uploaded_image_names = upload_images_to_server([generated_image])

                    # 将生成的截图路径存储到step的candidates字段
                    step.to_dict()["screenshot_options"] = ["http://3.145.59.104/pickimgjson/hl/" + name for name in
                                                            uploaded_image_names]

                    logger.success(f"Successfully processed step {step.id}")
                    return True
                else:
                    logger.warning(f"No screenshots generated for step {step.id} after all retry attempts")
                    return False

            except Exception as e:
                logger.error(f"Error processing step {step.id}: {e}")
                logger.debug(traceback.format_exc())
                return False


# def flows_to_excel(flow_dicts: list[dict], keyword, batch_index):
#     import pandas as pd
#
#     filename = f"{keyword}_flows_batch_{batch_index + 1:03d}_{TIMESTAMP}.xlsx"
#     file_dir = OUTPUT_DIR / f"{keyword}_{TIMESTAMP}"
#     file_dir.mkdir(parents=True, exist_ok=True)
#     file_path = file_dir / filename
#
#     df = pd.DataFrame(columns=['id', 'title', 'host'])
#
#     for flow_dict in flow_dicts:
#         data = []
#
#         # logger.debug(f"{flow_dict}")
#         data.append(flow_dict["id"])
#         # logger.debug(f"{data}")
#         data.append(flow_dict["title"])
#         # logger.debug(f"{data}")
#         for step in flow_dict["steps"]:
#             if step["host"]:
#                 data.append(step["host"])
#                 # logger.debug(f"{data}")
#                 df.loc[len(df)] = data
#                 break
#
#     df.to_excel(file_path, index=False)


def get_value_from_steps(flow: WebAgentFlow, key: str) -> str:
    for step in flow.steps:
        if not step.to_dict().get(key):
            continue

        return step.to_dict().get(key)

    return None


def flows_to_excel(flows: list[WebAgentFlow],
                   filename_keyword: str,
                   columns: list[str] = ["instruction", "instruction_id", "json_name", "url"],
                   batch_size: int = BATCH_SIZE):
    import pandas as pd
    import math

    def _create_excel_from_flows(flows: list[WebAgentFlow], batch_index: int = 0) -> str:
        """创建Excel文件并返回文件路径"""
        if batch_size > 0:
            filename = f"{filename_keyword}_flows_batch_{batch_index + 1:03d}_{TIMESTAMP}.xlsx"
        else:
            filename = f"{filename_keyword}_flows_{TIMESTAMP}.xlsx"

        file_dir = OUTPUT_DIR / f"{filename_keyword}_{TIMESTAMP}"
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
            logger.debug(f"{column}: {data}")

            data_rows.append(data)

        df = pd.DataFrame(data_rows, columns=columns)
        df.to_excel(file_path, index=False)
        return str(file_path)

    # flow_dicts = [flow.to_dict() for flow in flows]

    # 如果batch_size为0，不切割
    if batch_size == 0:
        file_path = _create_excel_from_flows(flows)
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

        file_path = _create_excel_from_flows(batch_flows, batch_index)
        created_files.append(file_path)
        print(f"批次 {batch_index + 1}/{num_batches} Excel文件已创建: {file_path}")

    return created_files


# def flows_to_json(dicts: list[dict], keyword: str = "remake"):
#     if not dicts:
#         logger.warning("No data to save")
#         return
#
#     total_batches = math.ceil(len(dicts) / BATCH_SIZE)
#     logger.info(f"Creating {total_batches} batch files with up to {BATCH_SIZE} flows each")
#
#     created_files = []
#     for batch_index in range(total_batches):
#         start_idx = batch_index * BATCH_SIZE
#         end_idx = min(start_idx + BATCH_SIZE, len(dicts))
#
#         batch_flows = dicts[start_idx:end_idx]
#
#         # flows_to_excel(batch_flows, keyword, batch_index)
#
#         filename = f"{keyword}_flows_batch_{batch_index + 1:03d}_{TIMESTAMP}.json"
#         file_dir = OUTPUT_DIR / f"{keyword}_{TIMESTAMP}"
#         file_dir.mkdir(parents=True, exist_ok=True)
#         file_path = file_dir / filename
#
#         with open(file_path, 'w', encoding='utf-8') as f:
#             json.dump(batch_flows, f, ensure_ascii=False, indent=4)
#
#         logger.success(f"Saved batch {batch_index + 1} with {len(batch_flows)} flows to {filename}")
#         created_files.append(file_path)
#         logger.info(f"Batch {batch_index + 1}: {len(batch_flows)} flows")
#
#     logger.success(f"All {total_batches} batch files created successfully")


def flows_to_json(flows: list[WebAgentFlow], filename_keyword: str, batch_size: int = BATCH_SIZE):
    # if not dicts:
    #     logger.warning("No data to save")
    #     return []

    def _create_json_from_flows(flows: list[WebAgentFlow], batch_index: int = 0) -> Path:
        """创建JSON文件并返回文件路径"""
        if batch_size > 0:
            filename = f"{filename_keyword}_flows_batch_{batch_index + 1:03d}_{TIMESTAMP}.json"
        else:
            filename = f"{filename_keyword}_flows_{TIMESTAMP}.json"

        file_dir = OUTPUT_DIR / f"{filename_keyword}_{TIMESTAMP}"
        file_dir.mkdir(parents=True, exist_ok=True)
        file_path = file_dir / filename

        flow_dicts = [flow.to_dict() for flow in flows]

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(flow_dicts, f, ensure_ascii=False, indent=4)

        return file_path

    # 如果batch_size为0，不切割
    if batch_size == 0:
        file_path = _create_json_from_flows(flows)
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

        file_path = _create_json_from_flows(batch_flows, batch_index)
        created_files.append(file_path)

        logger.success(f"Saved batch {batch_index + 1} with {len(batch_flows)} flows to {file_path.name}")
        logger.info(f"Batch {batch_index + 1}: {len(batch_flows)} flows")

    logger.success(f"All {total_batches} batch files created successfully")
    return created_files

# def extract_and_export_certain_flows(
#         json_files: list[Path] | Generator[Path, None, None] | Path,
#         modify_json_name: bool,
#         extractor: Callable[[list[WebAgentFlow]], list[WebAgentFlow]],
#         experter: Callable[[list[WebAgentFlow]], list],
#         batch_size: int,
#         processor: Callable[[list[WebAgentFlow]], list],):
#     all_flows = json_to_flows(json_files)
#
#     certain_flows = extractor(all_flows, )
