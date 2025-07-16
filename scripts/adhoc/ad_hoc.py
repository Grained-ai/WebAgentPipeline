from modules.webagent_data_utils import WebAgentFlow, WebAgentStep
from modules.flow_utils.flow_ops import (json_to_flows,
                                         extract_non_rect_flows,
                                         flows_to_excel,
                                         flows_to_json,
                                         JSON_DIR,
                                         MODIFIED_JSON_FILES,
                                         SUBMITTED_JSON_DIR,
                                         dedup_flows_by_id,
                                         subtract_flows, dedup_flows_by_title,
                                         extract_redo_flows,
                                         json_to_flows_dict,
                                         extract_non_redo_flows, get_value_from_steps, OUTPUT_DIR, )
# from modules.feishu_utils.bitable_ops import insert_record, get_records
from loguru import logger
from pathlib import Path
import json
import pandas as pd
from collections import defaultdict
from datetime import datetime, date


def jun26_unrect_flows_in_modifyjson():

    json_dir = "/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/all_modification/modification/20250702/after_fix2"
    json_files = Path(json_dir).glob("*.json")
    flows = json_to_flows(json_files)

    # flows = json_to_flows(MODIFIED_JSON_FILES)
    flows = extract_non_rect_flows(flows)
    flows = dedup_flows_by_id(flows)
    flows = dedup_flows_by_title(flows)
    print(f"Found {len(flows)} non-rect flows")
    # flows_to_json(flows, "unrect")
    flows_to_excel(flows, "unrect", batch_size=0)

# def jun27_unsubmitted_batch_to_bitable():
#     json_dir = Path(r"C:\Users\11627\Downloads\GrainedAI\WebAgentPipeline\outputs\unsubmitted_20250626_113917")
#     json_files = json_dir.glob("*.json")
#
#     is_skip = True
#     for json_file in json_files:
#         flows = json_to_flows(json_file, False)
#         for flow in flows:
#             # if flow.id == 'e9NKtfofK2do0RBNfyxUG':
#             #     is_skip = False
#             #
#             # if is_skip:
#             #     continue
#
#             instruction = flow.title
#             instruction_id = flow.id
#             batch_id = json_file.stem
#             host = ''
#             for step in flow.steps:
#                 if not step.to_dict().get('host'):
#                     continue
#                 else:
#                     host = step.to_dict()['host']
#                     break
#             json_name = flow.to_dict()['modified_json_name'].split('.')[0]
#             to_upload = 'True'
#
#             logger.info(f"instruction_id: {instruction_id}, instruction: {instruction}, batch_id: {batch_id}, json_name: {json_name}, to_upload: {to_upload}")
#
#             fields = {
#                 'instructions': instruction,
#                 'batch id': batch_id,
#                 'json name': json_name,
#                 'website': host,
#                 'to_upload': to_upload
#             }
#
#             app_tokn = 'EkLqbaVqIaKM0Rs2wTacJk2SnAc'
#             table_id = 'tblq2mhgEogevmCl'
#             response = insert_record(app_tokn, table_id, fields)
#
#             print(json.dumps(fields, ensure_ascii=False, indent=4))
#             if not response['code']:
#
#                 print(f"Successes, {response['data']['record']}")
#             else:
#                 # print(old_instruction_id, instruction_id, instruction, json_name, record_id)
#                 print(f"Failed, {response['msg']}, {response['error']}")

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

    remain_flows = dedup_flows_by_id(remain_flows)
    remain_flows = dedup_flows_by_title(remain_flows)
    logger.debug(f"remain_flows: {len(remain_flows)}")
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
            {
                'field_name': 'last_modified_time',
                'operator': 'is',
                'value': ["TheLastWeek"]
            },
        ]
    }

    records = get_records(app_token, table_id, view_id, filter_item)[0]
    passed_unsubmitted_flows = []
    instruction_list = []
    for record in records:
        record_id = record["record_id"]

        filter_item = {
            'conjunction': 'and',
            'conditions': [
                {
                    'field_name': 'Parent items',
                    'operator': 'is',
                    'value': [record_id]
                },
                {
                    'field_name': 'status',
                    'operator': 'is',
                    'value': ["Redo"]
                },
            ]
        }

        instructions = record['fields']['instruction']
        instruction = "".join([instruction_item['text'] for instruction_item in instructions])
        instruction_list.append(instruction)

        sub_records = get_records(app_token, table_id, view_id, filter_item)[0]
        if len(sub_records) == 0:
            flow_id = "preprocessed_" + record['fields']["batch id"]
            instructions = record['fields']['instruction']
            instruction = "".join([instruction_item['text'] for instruction_item in instructions])

            for flow in unsubmitted_flows_dict[flow_id]:
                if instruction == flow.title:
                    passed_unsubmitted_flows.append(flow)
                    break

    # print(f"instruction_list: {len(instruction_list)}")
    # for instruction in instruction_list:
    #     if instruction not in [flow.title for flow in passed_unsubmitted_flows]:
    #         print(instruction)
    print(f"passed_unsubmitted_flows: {len(passed_unsubmitted_flows)}")
    flows_to_json(passed_unsubmitted_flows, f"passed_unsubmitted_flows", 30)

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

    TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"unrect_flows_{TIMESTAMP}.xlsx"

    file_dir = OUTPUT_DIR / f"unrect_flows_{TIMESTAMP}"
    file_dir.mkdir(parents=True, exist_ok=True)
    file_path = file_dir / filename

    df = pd.DataFrame(data_rows, columns=["instruction", "instruction_id", "json_name", "url", "unrect_number", "unrect_steps"])
    df.to_excel(file_path, index=False)

    # print(f"Found {len(non_rect_flows)} non-rect flows")
    # flows_to_json(flows, "unrect")
    # flows_to_excel(flows, "unrect", batch_size=0)




if __name__ == "__main__":
    jun26_unrect_flows_in_modifyjson()
    # jun27_unsubmitted_batch_to_bitable()
    # jun27_unrect_batch_to_excel()
    # jun27_unrect_select_or_drag()
    # jun30_agg_checked_unsubmitted_pass_flows()
    # jun30_agg_checked_unsubmitted_redo_flows()
    # jun30_extract_checked_unsubmitted_pass_flows()
    # jun30_extract_checked_unsubmitted_redo_flows_on_bitable()
    # jul1_check_non_rect_step_in_each_flow()
    # jul1_new_unrect_flows_in_modifyjson()

    # TODO: 要不要弄一个方法，传入json路径和提取类型func和保存方法func，最终再导出batch json