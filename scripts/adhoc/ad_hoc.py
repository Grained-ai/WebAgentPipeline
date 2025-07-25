from modules.feishu_utils.bitable_record import BitableRecord
from modules.general_utils import generate_random_id
from modules.flow_utils.flow_ops import (json_to_flows,
                                         extract_non_rect_flows,
                                         flows_to_excel,
                                         flows_to_json,
                                         JSON_DIR,
                                         MODIFIED_JSON_FILES,
                                         SUBMITTED_JSON_DIR,
                                         dedup_flows_by_id,
                                         subtract_flows,
                                         dedup_flows_by_title,
                                         extract_redo_flows,
                                         json_to_flows_dict,
                                         extract_non_redo_flows,
                                         get_value_from_steps,
                                         OUTPUT_DIR,
                                         MODIFIED_JSON_DIR,
                                         extract_non_img_flows,
                                         DELIVERED_JSON_DIR,
                                         DELIVERED_JSON_FILES,
                                         BATCH_SIZE,
                                         TIMESTAMP,
                                         extract_is_remake_flows,
                                         extract_single_frame_from_flows,
                                         extract_candidate_frames_from_flows,
                                         copy_pick_img_from_flows,
                                         REMOTE_IMG_DIRS,
                                         REMOTE_PROJ_DIR,
                                         REMOTE_RAW_IMG_DIR,
                                         REMOTE_MARKED_IMG_DIR)
from modules.feishu_utils.bitable_ops import insert_record, get_records, get_record_ids, delete_records, update_records, get_records_by_id
from modules.linux_utils.linux_utils import upload_images_to_server
from modules.webagent_data_utils import WebAgentFlow
from loguru import logger
from pathlib import Path
import json
import pandas as pd
from collections import defaultdict
from datetime import datetime, date
import math
import traceback


def extract_ids(path: Path) -> tuple[list[str], list[str]]:
    import pandas as pd

    if path.suffix == '.csv':
        df = pd.read_csv(path)
        recording_ids = df['recording_id'].dropna().to_list()

    else:
        df = pd.read_excel(path)

        recording_id_webms = df['recording_id'].to_list()
        recording_ids = [recording_id_webm.split(".")[0] for recording_id_webm in recording_id_webms]

    # print('recording_ids', recording_ids)
    # exit(0)

    old_instruction_ids = df['instruction_id'].to_list()

    return old_instruction_ids, recording_ids

def extract_id_flow_dict(flows: list[WebAgentFlow]) -> dict[str, WebAgentFlow]:
    id_flow_dict = {}

    for flow in flows:
        for step in flow.steps:
            if step.recording_id:
                id_flow_dict[step.recording_id] = flow
                break
    print(json.dumps({key: value.id for key, value in id_flow_dict.items()}, indent=4))
    return id_flow_dict

INPUT_JSON_FILE = Path(r'C:\Users\11627\Downloads\GrainedAI\WebAgentPipeline\temp\a666_redo_flows_batch_20250704_182929.json')
input_flows = json_to_flows([INPUT_JSON_FILE])

def df_to_excel(data_rows: list,
                filename_keyword: str,
                columns: list[str] = ["instruction", "instruction_id", "json_name", "url"],
                batch_size: int = BATCH_SIZE):

    def _create_excel_from_df(rows: list, filename: str) -> str:
        """创建Excel文件并返回文件路径"""
        file_dir = OUTPUT_DIR / f"{filename_keyword}_{TIMESTAMP}"
        file_dir.mkdir(parents=True, exist_ok=True)
        file_path = file_dir / filename

        df = pd.DataFrame(rows, columns=columns)
        df.to_excel(file_path, index=False)
        return str(file_path)

    # 如果batch_size为0，不切割
    if batch_size == 0:
        filename = f"{filename_keyword}_flows_{TIMESTAMP}.xlsx"
        file_path = _create_excel_from_df(data_rows, filename)
        print(f"Excel文件已创建: {file_path}")
        return [file_path]

    # 计算需要切割的批次数
    total_data = len(data_rows)
    num_batches = math.ceil(total_data / batch_size)
    created_files = []

    # 切割并创建多个Excel文件
    for batch_index in range(num_batches):
        start_idx = batch_index * batch_size
        end_idx = min(start_idx + batch_size, total_data)
        batch_data = data_rows[start_idx:end_idx]

        filename = f"{filename_keyword}_flows_batch_{batch_index + 1:03d}_{TIMESTAMP}.xlsx"
        file_path = _create_excel_from_df(batch_data, filename)
        created_files.append(file_path)
        print(f"批次 {batch_index + 1}/{num_batches} Excel文件已创建: {file_path}")

    return created_files

def jun17_extract_flows_images():
    video_dir = Path(r"C:\Users\dehan\Desktop")

    upload_images = []
    for json_dir in [Path(r"C:\Users\dehan\Desktop\WedAgentPipeline_hl\jsons\final_dash_jsons")]:
        for json_file in json_dir.rglob("nytimes_2025-07-08_part_1.json"):
            logger.info(f"Processing {json_file.name}")

            flows = json_to_flows([json_file], modify_json_name=False)
            upload_images.extend(extract_single_frame_from_flows(flows, video_dir))

            json_flow = []
            for flow in flows:
                json_flow.append(flow.to_dict())

            output_file = OUTPUT_DIR / f"{json_file.parent.name}.json"
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(json.dumps(json_flow, ensure_ascii=False, indent=4))
                logger.info(f"Successfully wrote {output_file}")
            except Exception as e:
                logger.error(f"Failed to write {output_file}: {e}")
                logger.error(traceback.format_exc())

    # img_files = IMG_OUTPUT_DIR.rglob("*.jpeg")
    upload_images_to_server(upload_images)

def jun26_unrect_flows_in_modifyjson():

    json_dir = JSON_DIR / "modified_jsons_0701_after_Bill_bbox"
    json_files = json_dir.glob("*.json")
    flows = json_to_flows(json_files)

    # flows = json_to_flows(MODIFIED_JSON_FILES)
    flows = extract_non_rect_flows(flows)
    flows = dedup_flows_by_id(flows)
    flows = dedup_flows_by_title(flows)
    print(f"Found {len(flows)} non-rect flows")
    # flows_to_json(flows, "unrect")
    flows_to_excel(flows, "unrect", batch_size=0)

def jun27_unsubmitted_batch_to_bitable():
    json_dir = Path(r"C:\Users\11627\Downloads\GrainedAI\WebAgentPipeline\outputs\unsubmitted_20250626_113917")
    json_files = json_dir.glob("*.json")

    is_skip = True
    for json_file in json_files:
        flows = json_to_flows(json_file, False)
        for flow in flows:
            # if flow.id == 'e9NKtfofK2do0RBNfyxUG':
            #     is_skip = False
            #
            # if is_skip:
            #     continue

            instruction = flow.title
            instruction_id = flow.id
            batch_id = json_file.stem
            host = ''
            for step in flow.steps:
                if not step.to_dict().get('host'):
                    continue
                else:
                    host = step.to_dict()['host']
                    break
            json_name = flow.to_dict()['modified_json_name'].split('.')[0]
            to_upload = 'True'

            logger.info(f"instruction_id: {instruction_id}, instruction: {instruction}, batch_id: {batch_id}, json_name: {json_name}, to_upload: {to_upload}")

            fields = {
                'instructions': instruction,
                'batch id': batch_id,
                'json name': json_name,
                'website': host,
                'to_upload': to_upload
            }

            app_tokn = 'EkLqbaVqIaKM0Rs2wTacJk2SnAc'
            table_id = 'tblq2mhgEogevmCl'
            response = insert_record(app_tokn, table_id, fields)

            print(json.dumps(fields, ensure_ascii=False, indent=4))
            if not response['code']:

                print(f"Successes, {response['data']['record']}")
            else:
                # print(old_instruction_id, instruction_id, instruction, json_name, record_id)
                print(f"Failed, {response['msg']}, {response['error']}")

def jun27_unrect_batch_to_excel():
    json_dir = Path(r"C:\Users\11627\Downloads\GrainedAI\WebAgentPipeline\outputs\unrect_20250626_182719")
    json_files = json_dir.glob("*.json")

    flows = json_to_flows(json_files, False)

    columns = ['instruction', 'instruction_id', 'json_name', 'url']
    flows_to_excel(flows, columns, "unrect", batch_size=0)

def jun27_unrect_select_or_drag():
    all_json_dir = Path(r"C:\Users\11627\Downloads\GrainedAI\WebAgentPipeline\outputs\select_or_drag_20250613_182730")
    all_json_files = all_json_dir.glob("*.json")
    all_flows = json_to_flows(all_json_files, False)

    sub1_json_files = Path(r"C:\Users\11627\Downloads\GrainedAI\WebAgentPipeline\temp\redo_is_remake_1.json")
    sub1_flows = json_to_flows(sub1_json_files, False)

    sub2_json_files = SUBMITTED_JSON_DIR.glob("*06-24*.json")
    sub2_flows = json_to_flows(sub2_json_files, False)

    sub3_json_files = (JSON_DIR / "temp_jsons").rglob("*.json")
    sub3_flows = json_to_flows(sub3_json_files, False)
    sub3_flows = extract_redo_flows(sub3_flows)

    sub4_json_files = SUBMITTED_JSON_DIR.glob("*.json")
    sub4_flows = json_to_flows(sub4_json_files, False)

    remain_flows = subtract_flows(all_flows, sub1_flows)
    logger.info(f"1st remain_flows: {len(remain_flows)}")
    remain_flows = subtract_flows(remain_flows, sub2_flows)
    logger.info(f"2nd remain_flows: {len(remain_flows)}")
    remain_flows = subtract_flows(remain_flows, sub3_flows)
    logger.info(f"3rd remain_flows: {len(remain_flows)}")
    remain_flows = subtract_flows(remain_flows, sub4_flows)
    logger.info(f"4th remain_flows: {len(remain_flows)}")

    # remain_flows = dedup_flows_by_id(remain_flows)
    # remain_flows = dedup_flows_by_title(remain_flows)
    # logger.debug(f"remain_flows: {len(remain_flows)}")
    #
    # flows_to_json(remain_flows, "unknown_7", 0)

    # flows_to_excel(remain_flows, columns=['instruction', 'instruction_id', 'url', 'annotator'], filename_keyword='remark', batch_size=0)

def jun30_agg_checked_unsubmitted_pass_flows():
    UNSUBMITTED_JSON_DIR = JSON_DIR / "preprocessed_unsubmitted_jsons"
    UNSUBMITTED_JSON_FILES = UNSUBMITTED_JSON_DIR.glob("*.json")
    unsubmitted_flows_dict = json_to_flows_dict(UNSUBMITTED_JSON_FILES, modify_json_name=False)
    # print(unsubmitted_flows_dict.keys())

    INPUT_EXCEL_FILE = Path(r"C:\Users\11627\Downloads\GrainedAI\WebAgentPipeline\temp\QC_WebAgent_任务总表.xlsx")
    df = pd.read_excel(INPUT_EXCEL_FILE, sheet_name="Sheet2")

    passed_unsubmitted_flows = defaultdict(list)
    for index, row in df.iterrows():
        status = row["status"]

        if status == "Pass":
            quality_checker = row["quality_checked_by"]
            flow_id = "preprocessed_" + row["batch id"]
            print(flow_id, "flow_id")
            instruction = row["Parent items"]

            for flow in unsubmitted_flows_dict[flow_id]:
                if instruction == flow.title:
                    passed_unsubmitted_flows[quality_checker].append(flow)
                    break

    print(f"passed_unsubmitted_flows: {len(passed_unsubmitted_flows)}")
    print(passed_unsubmitted_flows)

    for quality_checker, flows in passed_unsubmitted_flows.items():
        print(f"quality_checker: {quality_checker}, passed_unsubmitted_flows: {len(flows)}")
        flows_to_json(flows, f"{quality_checker}_passed_unsubmitted_flows", 30)

def jun30_agg_checked_unsubmitted_redo_flows():
    UNSUBMITTED_JSON_DIR = JSON_DIR / "preprocessed_unsubmitted_jsons"
    UNSUBMITTED_JSON_FILES = UNSUBMITTED_JSON_DIR.glob("*.json")
    unsubmitted_flows_dict = json_to_flows_dict(UNSUBMITTED_JSON_FILES, modify_json_name=False)
    # print(unsubmitted_flows_dict.keys())

    INPUT_EXCEL_FILE = Path(r"C:\Users\11627\Downloads\GrainedAI\WebAgentPipeline\temp\QC_WebAgent_任务总表.xlsx")
    df = pd.read_excel(INPUT_EXCEL_FILE, sheet_name="Sheet2")

    redo_unsubmitted_flows = []
    for index, row in df.iterrows():
        status = row["status"]

        if status == "Redo":
            # quality_checker = row["quality_checked_by"]
            flow_id = "preprocessed_" + row["batch id"]
            instruction = row["Parent items"]

            for flow in unsubmitted_flows_dict[flow_id]:
                if instruction == flow.title:
                    redo_unsubmitted_flows.append(flow)
                    break

    print(f"passed_unsubmitted_flows: {len(redo_unsubmitted_flows)}")
    print(redo_unsubmitted_flows)

    flows_to_json(redo_unsubmitted_flows, f"redo_unsubmitted_flows", 30)
    flows_to_excel(redo_unsubmitted_flows, f"redo_unsubmitted_flows", batch_size=30)

def jun30_extract_checked_unsubmitted_pass_flows():
    UNSUBMITTED_JSON_DIR = JSON_DIR / "preprocessed_unsubmitted_jsons"
    UNSUBMITTED_JSON_FILES = UNSUBMITTED_JSON_DIR.glob("*.json")
    unsubmitted_flows_dict = json_to_flows_dict(UNSUBMITTED_JSON_FILES, modify_json_name=False)
    # print(unsubmitted_flows_dict.keys())

    INPUT_EXCEL_FILE = Path(
        r"C:\Users\11627\Downloads\GrainedAI\WebAgentPipeline\temp\QC_WebAgent_任务总表_任务总表.xlsx")
    df = pd.read_excel(INPUT_EXCEL_FILE)

    passed_unsubmitted_flows = []
    for index, row in df.iterrows():
        last_modified_time = row["last_modified_time"]
        parent_items = row["Parent items"]
        instruction = row["instruction"]

        condition = last_modified_time.date() >= date(2025, 6, 27) and pd.isna(parent_items) and instruction
        if condition:
            sub_df = df[df['Parent items'] == instruction]

            is_pass = True
            for sub_index, sub_row in sub_df.iterrows():
                status = sub_row["status"]
                if status == "Redo":
                    is_pass = False
                    break

            if is_pass:
                flow_id = "preprocessed_" + row["batch id"]
                instruction = row["instruction"]

                for flow in unsubmitted_flows_dict[flow_id]:
                    if instruction == flow.title:
                        passed_unsubmitted_flows.append(flow)
                        break

        # if condition and status == "Pass":
        #     print(last_modified_time.date(), parent_items)
        #     flow_id = "preprocessed_" + row["batch id"]
        #     instruction = row["instruction"]
        #
        #     for flow in unsubmitted_flows_dict[flow_id]:
        #         if instruction == flow.title:
        #             passed_unsubmitted_flows.append(flow)
        #             break

    # print(f"passed_unsubmitted_flows: {len(passed_unsubmitted_flows)}")
    # print(passed_unsubmitted_flows)

    print(f"passed_unsubmitted_flows: {len(passed_unsubmitted_flows)}")
    flows_to_json(passed_unsubmitted_flows, f"passed_unsubmitted_flows", 30)

def jun30_extract_checked_unsubmitted_redo_flows_on_bitable():
    UNSUBMITTED_JSON_DIR = JSON_DIR / "preprocessed_unsubmitted_jsons"
    UNSUBMITTED_JSON_FILES = UNSUBMITTED_JSON_DIR.glob("*.json")
    unsubmitted_flows_dict = json_to_flows_dict(UNSUBMITTED_JSON_FILES, modify_json_name=False)

    app_token = "EkLqbaVqIaKM0Rs2wTacJk2SnAc"
    table_id = "tblm5UwRFxRkR9aY"
    view_id = "vewQ01vkC7"

    filter_item = {
        'conjunction': 'and',
        'conditions': [
            {
                'field_name': 'Parent items',
                'operator': 'isEmpty',
                'value': []
            },
            {
                'field_name': 'status',
                'operator': 'is',
                'value': ["Pass"]
            },
        ]
    }

    records = get_records(app_token, table_id, view_id, filter_item)
    passed_unsubmitted_flows = []
    instruction_list = []
    for record in records:
        filter_item = {
            'conjunction': 'and',
            'conditions': [
                {
                    'field_name': 'Parent items',
                    'operator': 'is',
                    'value': [record.record_id]
                },
                {
                    'field_name': 'status',
                    'operator': 'is',
                    'value': ["Redo"]
                },
            ]
        }

        instruction_list.append(record.instruction)

        sub_records = get_records(app_token, table_id, view_id, filter_item)
        if len(sub_records) == 0:
            flow_id = "preprocessed_" + record.get_value("batch id")
            print(flow_id)

            for flow in unsubmitted_flows_dict[flow_id]:
                if record.instruction == flow.title:
                    passed_unsubmitted_flows.append(flow)
                    break

    print(f"instruction_list: {len(instruction_list)}")
    # for instruction in instruction_list:
    #     if instruction not in [flow.title for flow in passed_unsubmitted_flows]:
    #         print(instruction)
    print(f"passed_unsubmitted_flows: {len(passed_unsubmitted_flows)}")
    # flows_to_json(passed_unsubmitted_flows, f"passed_unsubmitted_flows", 30)

def jul1_check_non_rect_step_in_each_flow():
    non_rect_dir = Path(r"C:\Users\11627\Downloads\GrainedAI\WebAgentPipeline\outputs\unrect_20250701_110649")
    non_rect_jsons = non_rect_dir.glob("*.json")
    json_count_dict = defaultdict(int)

    # non_rect_flows = json_to_flows(non_rect_jsons, modify_json_name=False)
    for non_rect_json in non_rect_jsons:
        flows = json_to_flows(non_rect_json, modify_json_name=False)

        print(f"Searching in {non_rect_json.name}......")

        for flow in flows:
            has_rect_step = False

            print(f"    Searching in {flow.id} {flow.title[0:50]}......")
            for step in flow.steps:
                if step.type not in ['press_enter', 'back', 'cache', 'paste', 'end',
                                     'launchApp'] and step.title.lower() not in [
                    'end']:
                    if not step.adjusted_rect and not step.recrop_rect:
                        print(f"        Found Non Rect Step: {step.id} {step.title}...")
                        print(step.to_dict())
                        has_rect_step = True

                        json_count_dict[flow.to_dict()["modified_json_name"]] += 1

                        break

            if not has_rect_step:
                print(f"        Not Found Non Rect Step")

    # print(f"non rect flows: {len(non_rect_flows)}")
    print(json.dumps(json_count_dict, ensure_ascii=False, indent=4))

def jul1_new_unrect_flows_in_modifyjson():
    flows = json_to_flows(MODIFIED_JSON_FILES)
    flows = extract_non_rect_flows(flows)
    flows = dedup_flows_by_id(flows)
    flows = dedup_flows_by_title(flows)

    # df = pd.DataFrame(columns=["instruction", "instruction_id", "json_name", "url", "unrect_number", "unrect_steps"])

    data_rows = []
    for flow in flows:
        data = []
        first_unrect_step = True
        for idx, step in enumerate(flow.steps):
            if step.type.lower() not in ['press_enter', 'back', 'cache', 'paste', 'end',
                                         'launchapp'] and step.title.lower() not in [
                'end']:
                if not step.adjusted_rect and not step.recrop_rect:
                    # non_rect_flows.append(flow)
                    # break
                    if first_unrect_step:
                        data.append(flow.title)
                        data.append(flow.id)
                        data.append(flow.to_dict()["modified_json_name"])
                        data.append(get_value_from_steps(flow, "host"))
                        data.append([idx + 1])
                        data.append([step.title])

                        first_unrect_step = False
                    else:
                        data[4].append(idx + 1)
                        data[5].append(step.title)
        data_rows.append(data)

    filename = f"unrect_flows_{TIMESTAMP}.xlsx"

    file_dir = OUTPUT_DIR / f"unrect_flows_{TIMESTAMP}"
    file_dir.mkdir(parents=True, exist_ok=True)
    file_path = file_dir / filename

    df = pd.DataFrame(data_rows, columns=["instruction", "instruction_id", "json_name", "url", "unrect_number", "unrect_steps"])
    df.to_excel(file_path, index=False)

    # print(f"Found {len(non_rect_flows)} non-rect flows")
    # flows_to_json(flows, "unrect")
    # flows_to_excel(flows, "unrect", batch_size=0)

def jul3_bitable_pipeline_checking_delete_ops():
    app_token = "EkLqbaVqIaKM0Rs2wTacJk2SnAc"
    table_id = "tbl5Ga8Rzp2vPpwu"
    view_id = "vewReN7KIA"

    filter_item = {
        'conjunction': 'and',
        'conditions': [
            {
                'field_name': 'Parent items',
                'operator': 'isNotEmpty',
                'value': []
            },
            {
                'field_name': 'json_name',
                'operator': 'is',
                'value': ["hyl_dIUyhsV9nae547pR9o8QA"]
            },
        ]
    }

    hyl_records = get_record_ids(app_token, table_id, view_id, filter_item)
    print(f"Found {len(hyl_records)} hyl records")
    print(hyl_records)
    delete_records(app_token, table_id, hyl_records)

def jul4_extract_answer_general_without_sub_redo_on_bitable():
    app_token = "EkLqbaVqIaKM0Rs2wTacJk2SnAc"
    table_id = "tbl5Ga8Rzp2vPpwu"
    view_id = "vewDFJemJa"  # todo_redo

    filter_item = {
        'conjunction': 'and',
        'conditions': [
            {
                'field_name': '是否重新标注过',
                'operator': 'is',
                'value': ["FALSE"]
            },
            {
                'field_name': 'if_pass',
                'operator': 'is',
                'value': ["false"]
            },
            {
                'field_name': 'Parent items',
                'operator': 'isNotEmpty',
                'value': []
            },
            {
                'field_name': 'checkpoint',
                'operator': 'is',
                'value': ["Answer General"]
            },
        ]
    }

    need_redo_answer_records = get_records(app_token, table_id, view_id, filter_item)
    print(f"Found {len(need_redo_answer_records)} need redo answers")

    without_redo_answer_flows = []
    data = []
    for need_redo_answer_record in need_redo_answer_records:
        instruction_id = need_redo_answer_record.instruction_id
        json_name = need_redo_answer_record.json_name

        json_file = MODIFIED_JSON_DIR / f"{json_name}.json"
        flows = json_to_flows(json_file)

        instruction = ""
        url = ""
        for flow in flows:
            if flow.id == instruction_id:
                url = get_value_from_steps(flow, "host")
                instruction = need_redo_answer_record.instruction or flow.title

                without_redo_answer_flows.append(flow)

        print([instruction_id, instruction, json_name, url, ""])
        data.append([instruction_id, instruction, json_name, url, ""])

    flows_to_excel(without_redo_answer_flows, "end_image", columns=["instruction_id", "instruction", "json_name", "url", "recording_id"])

def jul4_check_missing_images_on_ubuntu():
    modify_json_files = list(MODIFIED_JSON_DIR.glob("*.json"))
    flows = json_to_flows(modify_json_files)

    non_img_flows_1 = extract_non_img_flows(flows)  # 0. 按 id 匹配

    end_img_ids = jul4_end_image_check()  # 1. id是不是带note->的End Image
    non_img_flows_2 = [flow_id for flow_id in non_img_flows_1 if flow_id not in end_img_ids]

    redo_ids = {'avTJZLR_V3GrC6Zej4JZB', 'iGPtAHZUU5mFTj4wb_z-N', '3OofEguwR6SQ_j6lVquY-', 'kC7e_ezMrLeXFb6_-zDzO', 'TzaaRmAxXr-1V0GFrhtFL', 'ZRDPQeY7pD1rN7zQ2z8OL', 'NQGFPb2PdIHbnkxaqlGFF', '9Lf9sJQnRuh-oHZtd0jFA', 'KmsnuTyOMYq0PyRJbtNgM', 'FyVlFd43JWHoGM2tZobNA', '8bLIWKjxf89GDr1OAgHfZ', '109nhEZB8MLmmrDZCcjCf', 'h9MR5CQTETCbk2P1HiLJF', 'Obanv3eRpkbPdqEFX5kml', 'Xh-xFiaQxFckCttNbpEBu', 'LvCNp3RsnKh0VoS8F-adV', 'DHTKhg1RsYazZrCL0I09p', 'whrXbcKFrKeKZ7LWLyHkQ', '01GzBXE8QAieaFJvl58I5', 'xpapbnhU2eAKJ__EkH98L', 'ndXjVL4787n8LNX3M5JQ-', 'OiDxFQ6s0_nIeclsvmvA8', 'hPmtvNK2ouFTvqgsjMf2O', 'f4qiGH3wA4fsoynHcuIEA', 'TziL-I9GZCZDyDJRnMjJB', 'zI-HlooK5M35D116SWyMi', '2lyQm-Mp57mafQUIzTPxB', '1BLkNsDZC30XrTTzSFXSW', 'Uam59X9OXm5ldNHCdtR14', 'kFaJftb76dPWT9FJ5rWX7', 'tV821tBv9jNadtpf9hqPD', 'tD9NDrhgrQ0JymycH_7iA', 'WevUqeJFRvYFRiwbEo04y', 'Grpsz-6mznPpzk7lZZmFw', 'VjjfiCUk-aJIaMQkXfzuz', '2hYO-D_2c2ISfWa1__OZf', 'Zr5Xv_IMjA3sagqeoDVQv', '4jMDnQ7E7Ny8yg-bBYrHz', 'Hc89VEEyZcCRROD09jXFR', 'bK9XvpEwo43TQPlL-20uh', 'khiG9vKWaMjxQo4ld1Kan', '1TgIrvy5qlme6dUWen6fo', 'KKLAyLGC_fkmKBBP5dMUP', 'ymq-b3ICLLwS-pXn3W8vL', 'Y7TQDYWjLLgv7pf8O0Bfe', 'l0fwNJhDzN8ewDj6uhQVF', 'zqJ39_WGkasH7G2bytqTx', 'Nl7relU0BZgcffB_tnXUO', 'i64-kFW8FpUSVTv5QW2Ni', 'rucLfBiHLG7DUWhYmUPfg', 'acBs29Oo9N2QOD32XIWc3', '7WG2Pq3WvaDAaT3Obe_ze', 'z43Vi-DpLQT1xlk4zCRHS', 'QNqRIv38_4nRBmR_r5Qoj', '_Odt1xZfbVGHKpFtFUt-8', 'm6o3L1pfOKRGjKq_KFFE0', 'hpc0Wu1RudwW69WVPHm1G', 'TFRkY9cwo54_r91NpBjIx', 'aa7OJH9oeaNUeR_LTgxY7', 'bh49j153VqgCmyUpm8FXK', 'Y3Cqu0cD09946waxHIgP0', 'w42mpt5WBDUhkkdqMSHN2', 'UcEUn5wqPSvLgm_B1vX5d', 'mOgWPE3VZM2tBK4ZDbLWQ', 'lox4NgFBHzWTRI9KMxtHx', 'plBOcI2fuUbwv0676tC3G', 'x9IMOUmxyMrY0vPhMLb9S', '5Jdzn47aUPPrVgPGEw1Q8', 'AI6JJx_GAA5A7y0Zu17O3', 'e2aWce1e_Az-aHi3AlqSY', 'kXhsIGajzoziQdIipGAO3', 'sn3Uglpimlpri3vFzCPoe', 'KS-vcCtykWd9TNq-DJz_I', 'faPeTAaYxF2xJmWc625cP', 'i0frqL_GvTfzVt_R_5Kn5', 'vQYqajGQWucV35nRqivqE', 'X9GecA56UBA0r4WJ4Pm6O', 'GqdWcn1f6ewcJdNqoaqMQ', 'Q35N8b7jQMxaDYdmTvasV', 'v30--vW-xlNvlk47VeY62', '08dZMizSs3_oTfaGgF1Fz', 'm2GA-SwpjKXGF-5gf2Kh4', 'YjPqBaahTn6uk0-BltGoZ', 'wLq7svsp_Xxc0bQVnsuzl', 'gOORYKBuFAWfr66PSMMHU', '4O040c6TKobZeR1Nl6nf5', 'VuojtFU4iX8CHLTvC95lh', 'qh7j8AVbrygMsSXGLd5ud', '1YNd-CaECndASGPcQ89fM', '3I7Zkz7dpdvsgxR2xNw2n', '-HnjgN2Sz8DoMt7PH3YKN', 'eOM95I4btPkIK6HaAJi5l', 'C85Mu3ShWriYd7dzANQXz', 'EU-n2NK1pBkS6HgMCecEY', '7aITmNWY9GbDn6EgvtvAa', '9Z_19-A3vPSSRIL5QIUQ8', 'hT5zjY8BV9TnW14Vtz1Y3', '28rnm48tPGCPBKVR3Jg62', 'HWaCn3Scajz8N8NSRy3v1', 'LTBSFpwoox5IaT870EA42', 'kOqAFjE2IjWZoiUHTYMpV', 'PWrm-QAYi-rMdCoA62xQx', 'CDQXl_HIoThoXnMVe__T3', 'eiek-tc12zBhPsJOw48RT', 'HtueQJ93x5K8c9NP_4oTp', 'Cb0clWppbp9KrczIpzGoY', 'n1cHPgLVD5iRqEhuk7HjC', 'zIVlANbywlLZYyBcR5d8U', 'f_ByB6EChEkGoRWNKree8', 'IKduwCzu4E-nNfaYtRUEn', '0l-FVGQZlKkrX26Qx9Hwd', 'F_fzaLS59eOYw0RKne1vK', 'QBre-OYnDp2_u0paqReYB', 'ExiH124x3p95hXPyFU0bI', '01ekEGOp5PXIZ60zfIu41', '533FPcI4YfUdTOr1a_J3F', '5oQbBXKfc-xDyVpRNlRsT', 'xf0WcZTAQDvmv6HHCQUFS', 'Uwv_Yddc8FGKko0IC-Xr-', 'T10g0iN-HhxrHPqSjMwQM', 'X1S1juYvLnwObvYuZH9cx', 'a4DIPQsDkAd6K4TM8Gwm4', 'zNJLx6v-ti2eGzn1OtNfN', 'f3KWQ5fI8uAYayqXRcPs4', '6hjFZQ05Go2WuVBvfiZi8', 'USic5kF3Zbs3Cg2VYw7u-', 'D4vRtVQaxcEPXroHJMxu-', '6tLdm15_y-RnVqwiBXaFW', 'Dxy_s3PLrApHcYSxlMsPw', 'jkkpFLX6ISLWvqYVluFxY', 'A0Bla-A9jhcw3heq0A8rC', '2i-pDOW-3r_PWsLoz3Uks', 'NAUvmTPfY68i_XUxAk_b6', 'JiXfw1AxMK41QfOlj8YqC', 'WyzkBV1Zzi8rl3WIQCjlA', 'OPcfPhKIynoXtUO5mEpl0', '20I0n_JapNAYtDMhnkXbl', 'S6e00iGf2b0UE5ouOrsVa', 'Kuj2z2Kvjv8NiKclwArdC', 'Snx8t7sc_wT0VU8jac0NJ', '7Karhukm8I4uL8lSks19u', 'aw6FE0lUdSwFLs1onqucp', 'YF9TGV_MWG-qBg6EwGkx-', 'V9B7dwRIpyDCjYDegSOdL', 'SB8_tvoEGBnUfREgic7Al', 'LOAQtIjcRmYsCmuXclpxp', 'lYQHGSQL8tqUaK9Ex0omx', 'TjZcq1xx_oMduV4hLIi19', 'nE0_BITSwmRTVCj9EwSRs', 'oTlVPWW2h8APtkZVXKRpZ'}  # 2. 是不是redo
    non_img_flows_3 = [flow_id for flow_id in non_img_flows_2 if flow_id not in redo_ids]

    print(f"Found {len(non_img_flows_3)} non-image flows")

    # flows_to_json(non_img_flows_3, "non_img")

def jul4_end_image_check():
    app_token = "EkLqbaVqIaKM0Rs2wTacJk2SnAc"
    table_id = "tbl5Ga8Rzp2vPpwu"
    view_id = "vewReN7KIA"

    filter_item = {
        'conjunction': 'and',
        'conditions': [
            {
                'field_name': 'checkpoint',
                'operator': 'is',
                'value': ["End Image Check"]
            },
            # {
            #     'field_name': '涉及到的修改',
            #     'operator': 'is',
            #     'value': ["替换图"]
            # },
            {
                'field_name': 'Note',
                'operator': 'contains',
                'value': ["->"]
            },
        ]
    }

    end_image_records = get_records(app_token, table_id, view_id, filter_item)

    logger.info(f"Found {len(end_image_records)} end image records")

    flow_id = set()

    print_list = []

    for end_image_record in end_image_records:
        # print(end_image_record.instruction_id, end_image_record.note)

        instruction_id = end_image_record.instruction_id
        json_name = end_image_record.json_name
        note = end_image_record.note.split("; ")[-1]
        target_step_index, source_step_index = note.split("->")
        logger.info(f"{instruction_id} {json_name} {target_step_index} {source_step_index}")

        flow_id.add(instruction_id)

        json_file = MODIFIED_JSON_DIR / f"{json_name}.json"
        flows = json_to_flows(json_file)

        # if instruction_id not in [
        #     # "2hYO-D_2c2ISfWa1__OZf",
        #     # "01GzBXE8QAieaFJvl58I5",
        #     "x3GlUltrtf9WuZH4Y_6Qw",
        #     "pq8JvDpKmDTtd4QJw95Kp",
        #     "AcLGkhLG5MLUcuNg2ehmr",
        #     "TQI0LLlTCLSzyDSnpH9qK",
        #     "uV3BBQU87Xao03o56O3TY",
        #     "v_7vQmO0X7RiSgly8oGQ5",
        # ]:
        #     continue

        # flow_id = set()
        for flow in flows:
            if flow.id == instruction_id:
                target_step = flow.steps[int(target_step_index) - 1]
                source_step = flow.steps[int(source_step_index) - 1]

                print_list.append([
                    json_name.split("_")[0], flow.id, note
                ])



                # logger.info(f"Backuping {flow.id}-{target_step.id}-{source_step.id}")
                # logger.info(f"Backuping {json_name.split("_")[0]} {flow.id} {target_step.id} http://3.145.59.104/storage/frames_raw/{source_step.id}_marked.jpeg")
                # print(target_step.title, source_step.title)

                # # TODO:
                # # --1. 根据note，获取目标step的id和要被复制的step.id
                # # 2. img_dir下查找要目标的step.id开头的文件，都添加上_bak_日期
                # # 3. img_dir下查找要被复制的step.id开头的文件，复制一份修改成目标step.id
                #
                # for remote_img_dir in REMOTE_IMG_DIRS:
                #     backup_existing_images(None, remote_img_dir, target_step.id)
                #     replace_step_id_in_filenames(None, remote_img_dir, source_step.id, target_step.id)


                break

    for print_item in print_list:
        print(print_item)

    return flow_id

def jul7_extract_redo_on_bitable():
    app_token = "EkLqbaVqIaKM0Rs2wTacJk2SnAc"
    table_id = "tbl5Ga8Rzp2vPpwu"
    view_id = "vewReN7KIA"

    filter_item = {
        'conjunction': 'and',
        'conditions': [
            {
                'field_name': 'checkpoint',
                'operator': 'is',
                'value': ["Redo"]
            },
        ]
    }

    redo_records = get_records(app_token, table_id, view_id, filter_item)

    redo_ids = set([redo_record.instruction_id for redo_record in redo_records])
    print(redo_ids)

    return redo_ids

def jul8_add_router_to_bitable():
    app_token = "EkLqbaVqIaKM0Rs2wTacJk2SnAc"
    table_id = "tbl5Ga8Rzp2vPpwu"
    view_id = "vewReN7KIA"

    records = get_records(app_token, table_id, view_id)

    dedup_records = []
    ids = set()

    for record in records:
        if not record.instruction_id:
            continue

        instruction_id = record.instruction_id

        if instruction_id not in ids:
            dedup_records.append(record)
            ids.add(instruction_id)

    print(f"Found {len(dedup_records)} deduplicated records")
    # print(json.dumps(dedup_records, indent=4))

    all_flows = json_to_flows(DELIVERED_JSON_FILES)
    all_id_json_mapping = {flow.id: flow.to_dict()['modified_json_name'] for flow in all_flows}

    url_template = "http://3.145.59.104/agent_v2/{json_name}.json/{instruction_id}"

    updating_records = []
    count = 0
    for dedup_record in dedup_records:
        instruction_id = dedup_record.instruction_id
        json_name = dedup_record.json_name
        record_id = dedup_record.record_id
        print(instruction_id, json_name, record_id)

        json_file = DELIVERED_JSON_DIR / f"{json_name}.json"

        is_found = False

        if json_file.exists():
            flows = json_to_flows(json_file)
            for flow in flows:
                if flow.id == instruction_id:
                    count += 1
                    print(f"isFound: {instruction_id} - {json_name}, {count}/{len(dedup_records)}")

                    updating_record = {
                        "fields": {
                            "url": {
                                "link": url_template.format(json_name=json_name, instruction_id=instruction_id),
                                "text": "可视化"
                            }
                        },
                        "record_id": record_id
                    }

                    updating_records.append(updating_record)

                    is_found = True
                    break

        if not is_found:
            json_name = all_id_json_mapping[instruction_id]
            count += 1
            print(f"notFound: {instruction_id} - {json_name}, {count}/{len(dedup_records)}")

            updating_record = {
                "fields": {
                    "url": {
                        "link": url_template.format(json_name=json_name, instruction_id=instruction_id),
                        "text": "可视化"
                    }
                },
                "record_id": record_id
            }

            updating_records.append(updating_record)

    print(f"Found {len(updating_records)} update records")

    update_records(app_token, table_id, updating_records)

def jul8_find_records_with_redo():
    app_token = "EkLqbaVqIaKM0Rs2wTacJk2SnAc"
    table_id = "tbl5Ga8Rzp2vPpwu"
    view_id = "vewReN7KIA"

    filter_item = {
        'conjunction': 'and',
        'conditions': [
            {
                'field_name': 'checkpoint',
                'operator': 'is',
                'value': ["Redo"]
            },
            # {
            #     'field_name': 'instruction_id',
            #     'operator': 'isNotEmpty',
            #     'value': []
            # },
        ]
    }

    redo_records = get_records(app_token, table_id, view_id, filter_item)
    flow_ids = set()
    for redo_record in redo_records:

        while True:
            parent_record_id = redo_record.parent_record_id

            redo_record = get_records_by_id(app_token, table_id, [parent_record_id])[0]
            # print(parent_record)

            if not redo_record.parent_record_id:
                break

        if not redo_record.instruction_id:
            continue

        flow_ids.add(redo_record.instruction_id)

    print(flow_ids)

def jul9_repair_final_jsons():
    final_json_dir = Path(r"C:\Users\11627\Downloads\GrainedAI\WebAgentPipeline\jsons\final_dash_jsons")
    final_json_files = list(final_json_dir.glob("*.json"))

    launch_app_ids = [
        "3weUj-NKoAtQn8LG5DhlD",
        "sdxovQL7H9X9d8l-MEurq",
        "qbicmfUXd0a-iUC7iDkvM",
        "_LIaY9fyuzi5QXKhkuL9S",
        "weyu7VbOb_U8c-grS4njO",
        "QDFer3a8dCxUoYyOpP64V",
        "v7y_hD0O_g-xS3OTjPf4p",
        "tKwTkQvXBFjlszD158GIs",
        "fPCInjCoDKAQQIpgTkct-",
        "WdO6QOOmqzv8arTYlzdda",
        "AkGMqmT7RbRoxHZpUeOUu",
        "9MFE_tYNzhyK0oS59IfnJ",
        "9M-VidqVpPpKPqwoXkSeZ",
        "WJM17vjl5PmK5Z6BglO8P",
        "vkR2Nae8xhQjIsfWnDiHF",
        "skvRnITVPW_WMrtg0QMa3",
        "6Mxu2qQY2yDrbnXw15jpq",
        "A1YDIXg05MLjpR90OZOyr",
        "9AAXlVRhEVWZwptovceUv",
        "O8QiNMs-B7ZhmvX9vTssT",
    ]
    corrupted_instruction_ids = [
        "I1zw-40IeJ0yU1pgqV7QL",
        "K02Bgck4fhxE2ADJabbJx",
        "ojpQOqV5Z7Ytw0gmSoToi",
        "RoP_Dt1bk7RFMg6P4XGnT",
        "xtWCEKSdRWRV7EYXnxgze",
        "h-b8QR58W4mj0GcQ6Iezc",
        "1wxYef23qh7REA6OGhB-y",
        "EqVg34K1uqByzKXJ21tPB",
        "YOoCMgSYvU2GI0KdJOsBP",
        "PMY1npQHumCGHzYKcrHej",
        "Xei4VT6Modn2BeHW67_I1",
        "v_7vQmO0X7RiSgly8oGQ5",
    ]

    for json_file in final_json_files:
        flows = json_to_flows(json_file)

        for flow_idx, flow in enumerate(flows):
            if flow.id in launch_app_ids:
                for index, step in enumerate(flow.steps):
                    if step.title.lower().startswith("answer") and index > 0 and flow.steps[index - 1].type != "launchApp":
                        launch_app_step = {
                            'id': generate_random_id(len(flow.id)),
                            'href': step.to_dict()["host"],
                            'type': 'launchApp',
                            'title': 'launchApp',
                            'annotations': None,
                            # 'richLink': '',
                            'mock': True
                        }

                        flow.to_dict()["steps"].insert(index, launch_app_step)

        logger.debug("到这了")
        flows_to_json(flows, json_file.name, 0)

def jul10_extract_non_a666_images_id():
    excel_file = Path(r"C:\Users\11627\Downloads\GrainedAI\WebAgentPipeline\temp\a666_redo_flows_batch_20250704_182929.xlsx")
    df = pd.read_excel(excel_file)
    a666_ids = df["instruction_id"].to_list()
    print(a666_ids)

    app_token = "EkLqbaVqIaKM0Rs2wTacJk2SnAc"
    table_id = "tblZVFj6w6FfQyNb"
    view_id = "vewR89B6qG"

    records = get_records(app_token, table_id, view_id)

    for record in records:
        instruction_id = record.instruction_id

        if instruction_id not in a666_ids:
            print(instruction_id)

def jul10_insert_subrecord_to_final_dash():
    qc_file = Path(r"C:\Users\11627\Downloads\GrainedAI\WebAgentPipeline\temp\qc_a666_redo_flows.xlsx")
    df = pd.read_excel(qc_file)

    instruction_ids, target_recording_ids = extract_ids(qc_file)
    recording_id_flow_dict = extract_id_flow_dict(input_flows)

    app_token = "EkLqbaVqIaKM0Rs2wTacJk2SnAc"
    table_id = "tblZVFj6w6FfQyNb"
    view_id = "vewpjjwFUo"

    fields = []
    for row in df.itertuples():
        print(row)
        instruction_id = row.instruction_id
        instruction = row._6 if not pd.isna(row._6) else None
        recording_id = row.recording_id
        is_pass = row.is_pass
        质检操作 = row.质检操作.split("，") if not pd.isna(row.质检操作) else None
        note = row.note if not pd.isna(row.note) else None

        filter_item = {
            'conjunction': 'and',
            'conditions': [
                {
                    'field_name': 'instruction_id',
                    'operator': 'is',
                    'value': [instruction_id]
                }
            ]
        }

        record = get_records(app_token, table_id, view_id, filter_item)[0]
        record_id = record["record_id"]

        app_token = "EkLqbaVqIaKM0Rs2wTacJk2SnAc"
        table_id = "tblZVFj6w6FfQyNb"
        view_id = "vewpjjwFUo"

        field = {
            "instruction_id": recording_id_flow_dict[recording_id].id,
            "instruction": instruction,
            "json_name": "bali.json",
            "is_pass": is_pass,
            "质检操作（如果有）": 质检操作,
            "note": note,
            "Parent items": [record_id]
        }

        response = insert_record(app_token, table_id, field)

        print(response)

def jul10_candidate_list():
    video_dir = Path(r"C:\Users\dehan\Desktop")

    all_is_remake_flows = []
    upload_images = []
    for json_dir in [Path(r"C:\Users\11627\Downloads\GrainedAI\WebAgentPipeline\temp\0724_isRemake")]:
        for json_file in json_dir.rglob("*.json"):
            logger.info(f"Processing {json_file.name}")

            flows = json_to_flows([json_file], modify_json_name=False)
            upload_images.extend(extract_candidate_frames_from_flows(flows))

            all_is_remake_flows.extend(extract_is_remake_flows(flows, certain_steps_only=True))
            # json_flow = []
            # for flow in is_remake_flows:
            #     json_flow.append(flow.to_dict())
            #
            # output_file = OUTPUT_DIR / f"{json_file.name}"
            # try:
            #     with open(output_file, 'w', encoding='utf-8') as f:
            #         f.write(json.dumps(json_flow, ensure_ascii=False, indent=4))
            #     logger.info(f"Successfully wrote {output_file}")
            # except Exception as e:
            #     logger.error(f"Failed to write {output_file}: {e}")
            #     logger.error(traceback.format_exc())
    flows_to_json(all_is_remake_flows, "rest_52_remake")

    # img_files = IMG_OUTPUT_DIR.rglob("*.jpeg")
    upload_images_to_server(upload_images, candidates=True)

def jul18_bitable_record_test():
    app_token = "EkLqbaVqIaKM0Rs2wTacJk2SnAc"
    table_id = "tbl5Ga8Rzp2vPpwu"
    view_id = "vewDFJemJa"  # todo_redo

    filter_item = {
        'conjunction': 'and',
        'conditions': [
            {
                'field_name': '是否重新标注过',
                'operator': 'is',
                'value': ["FALSE"]
            },
            {
                'field_name': 'if_pass',
                'operator': 'is',
                'value': ["false"]
            },
            {
                'field_name': 'Parent items',
                'operator': 'isNotEmpty',
                'value': []
            },
            {
                'field_name': 'checkpoint',
                'operator': 'is',
                'value': ["Answer General"]
            },
        ]
    }

    need_redo_answer_records: list[BitableRecord] = get_records(app_token, table_id, view_id, filter_item)
    print([record.parent_record_id for record in need_redo_answer_records])

def jul21_rest_instruction_batch():
    target_file = Path(r"C:\Users\11627\Downloads\GrainedAI\WebAgentPipeline\temp\QC_WebAgent_缺漏检查_待确认.xlsx")
    target_df = pd.read_excel(target_file)

    all_files = [Path(r"C:\Users\11627\Downloads\GrainedAI\WebAgentPipeline\temp\英文指令-Grained-0313.xlsx"), Path(r"C:\Users\11627\Downloads\GrainedAI\WebAgentPipeline\temp\英文指令_Grained_0317.xlsx")]
    all_dfs = [pd.read_excel(file) for file in all_files]
    all_df = pd.concat(all_dfs, ignore_index=True)

    data = []
    for row in all_df.itertuples():
        row_data = []
        for target_row in target_df.itertuples():
            if target_row.instruction == row.指令:
                row_data.extend([target_row.instruction, row.网站])
                print(target_row.instruction, row.网站)

                data.append(row_data)
                break

    df_to_excel(data, "rest_instruction", columns=["instruction", "url"])

def jul21_extract_non_rect_flows_test():
    json_dir = JSON_DIR / "modified_jsons_0701_after_Bill_bbox"
    json_files = json_dir.glob("*.json")
    flows = json_to_flows(json_files)

    flows = extract_non_rect_flows(flows)
    extract_redo_flows(flows)

    flows_to_json(flows, "test_non_rect")

def jul25_copy_pick_img_from_flows():
    json_dir = Path(r"C:\Users\11627\Downloads\GrainedAI\WebAgentPipeline\temp\0725_pickimgs")
    json_files = json_dir.glob("*.json")
    flows = json_to_flows(json_files)

    copy_pick_img_from_flows(flows)

    for flow in flows:
        for step in flow.steps:
            img_save = step.to_dict().get("imgSave").replace("frames_marked", "frames_raw").replace("_marked", f"_scaled{'2' if step.timestamp < 0 else ''}")
            step.to_dict()["imgSave"] = img_save

    flows_to_json(flows, "rest_52_remake")

if __name__ == "__main__":
    # jun17_extract_flows_images()                               # flows跑mp4/webm截帧
    # jun26_unrect_flows_in_modifyjson()                         # 提取modifyjson/下没有拉框的flow
    # jun27_unsubmitted_batch_to_bitable()                       # 上传未提交的blow到多维表
    # jun27_unrect_batch_to_excel()                              # 未拉框的flow转换成excel
    # jun27_unrect_select_or_drag()                              # 提取未拉框的flow中是select or drag的（涉及原生下拉框）
    # jun30_agg_checked_unsubmitted_pass_flows()                 # 根据多维表pass记录，提取未提交flow中pass的
    # jun30_agg_checked_unsubmitted_redo_flows()                 # 根据多维表redo记录，提取未提交flow中redo的
    # jun30_extract_checked_unsubmitted_pass_flows()             # 根据多维表pass记录，提取未提交flow中pass的
    # jun30_extract_checked_unsubmitted_redo_flows_on_bitable()  # 根据多维表redo记录，提取未提交flow中redo的
    # jul1_check_non_rect_step_in_each_flow()                    # 提取modifyjson/下没有拉框的step
    # jul1_new_unrect_flows_in_modifyjson()                      # 提取modifyjson/下没有拉框的flow
    # jul3_bitable_pipeline_checking_delete_ops()                # 多维表删除record
    # jul4_extract_answer_general_without_sub_redo_on_bitable()  # 多维表提取answer general且没有子行的record
    # jul4_check_missing_images_on_ubuntu()                      # Ubuntu上查找缺失的图片
    # jul4_end_image_check()                                     # 提取多维表上涉及end image check的
    # jul7_extract_redo_on_bitable()                             # 提取多维表上需要redo的
    # jul8_add_router_to_bitable()                               # 多维表上的record更新标注平台路由地址
    # jul8_find_records_with_redo()                              # 查找需要redo的record
    # jul9_repair_final_jsons()                                  # 最终冲刺jsons，在没有launchapp的answer step前添加launchapp
    # jul10_extract_non_a666_images_id()                         # 提取a666标注的flow
    # jul10_insert_subrecord_to_final_dash()                     # 插入子行到多维表
    # jul10_candidate_list()                                     # 截图candidates
    # jul21_rest_instruction_batch()                             # 剩余的query匹配总表获取url，再转化成json batch
    # jul21_extract_non_rect_flows_test()                        # extract_non_rect_flows()单元测试
    jul25_copy_pick_img_from_flows()                             # 将isremake steps的图片替换原本的图片，并且imgSave字段从marked图片改成scaled图片
