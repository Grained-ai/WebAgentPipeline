import csv
import glob
import json
from pathlib import Path
from collections import defaultdict
from typing import Optional, List
from modules.webagent_data_utils import WebAgentFlow
import math
from loguru import logger


def load_instructions_and_json(json_paths: list):
    """
    加载所有的 JSON 文件，并将每个 JSON 的 title 对应的记录按 instruction 聚合
    :param json_paths: JSON 文件路径列表
    :return: 按 instruction 聚合的字典 {instruction -> list of JSON records}
    """
    instruction_map = defaultdict(list)

    for json_path in json_paths:
        with open(json_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"无法读取文件 {json_path}: {e}")
                continue

        # 遍历 JSON 中的每个条目
        for entry in data:
            title = entry.get('title', "").strip()
            instruction_map[title].append(entry)  # 按 instruction 聚合 JSON 条目

    return instruction_map


def group_by_actiontodo_and_instructions(csv_path: Path, instruction_map: dict,
                                         target_actiontodo_names: Optional[List[str]] = None,
                                         exclude_actiontodo_names: Optional[List[str]] = None,
                                         allow_multiple_todo_name: Optional[bool] = None,
                                         target_batch: Optional[List[str]] = None,
                                         exclude_entries_jsons: Optional[List[Path]] = None):
    """
    根据 CSV 文件中的 ActionTodo 聚合对应的 JSON 记录
    :param csv_path: CSV 文件路径
    :param instruction_map: 已加载的 JSON 文件中的 instruction 到记录的映射
    :param target_actiontodo_names: 需要聚合的 ActionTodo 名称
    :param allow_multiple_todo_name: 是否允许多个 ActionTodo 匹配
    :return: 聚合后的 JSON 记录
    """
    # 读取 CSV 文件内容
    all_csv_data = {}
    json_name_batch_map = {}  # 存储每个 jsonname 对应的 batch_id
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            actiontodo_string = row['ActionTodo'].strip()
            actiontodos = [todo.strip() for todo in actiontodo_string.split(',')]

            instruction = row['instruction'].strip()
            jsonname = row['json_name'].strip()
            batch_id = row['batch id'].strip()
            parent_items = row['Parent items'].strip()
            if parent_items not in all_csv_data:
                all_csv_data[parent_items] = {}
            if jsonname not in all_csv_data[parent_items]:
                all_csv_data[parent_items][jsonname] = {
                    'ActionTodo': [],
                    'instruction': [],
                }
            all_csv_data[parent_items][jsonname]['ActionTodo'].extend(actiontodos)
            if instruction:
                all_csv_data[parent_items][jsonname]['instruction'].append(instruction)

            json_name_batch_map[jsonname] = batch_id  # 映射 jsonname 到 batch_id


    if exclude_entries_jsons:
        exclude_entries = []
        for json_path in exclude_entries_jsons:
            with open(json_path, 'r') as f:
                data = json.load(f)
            for d in data:
                flow_ins = WebAgentFlow(d)
                exclude_entries.append(flow_ins.title)
    else:
        exclude_entries = []
    logger.info(f"Need to exclude: {len(exclude_entries)} entries")

    # 处理每条 CSV 记录，更新对应的 JSON 记录
    aggregated_data = []
    for instruction in all_csv_data:
        skip_instruction = False
        if instruction in exclude_entries:
            logger.warning(f"SKIPPED: {instruction}. In exclude files.")
            continue
        for jsonname in all_csv_data[instruction]:
            row = all_csv_data[instruction][jsonname]
            actiontodos = row['ActionTodo']
            instruction_records = row['instruction']
            batch_id = json_name_batch_map[jsonname]
            if target_batch:
                if batch_id not in target_batch:
                    skip_instruction = True
                    break
            if exclude_actiontodo_names:
                next_row = False
                for item in exclude_actiontodo_names:
                    if item in actiontodos:
                        next_row = True
                        break
                if next_row:
                    skip_instruction = True
                    break

            if target_actiontodo_names:
                next_row = False
                for item in target_actiontodo_names:
                    if item not in actiontodos:
                        next_row = True
                        break
                if next_row:
                    skip_instruction = True
                    break
                if not allow_multiple_todo_name and len(actiontodos) > len(target_actiontodo_names):
                    skip_instruction = True
                    break
            # 查找对应的 JSON 记录
            json_records = instruction_map.get(instruction, [])

            if json_records:
                # 遍历找到的所有 JSON 记录并更新 fix_methods
                for entry in json_records:
                    fix_methods = entry.get('fix_methods', [])

                    for todo in actiontodos:
                        if todo not in fix_methods:
                            fix_methods.append(todo)
                    entry['fix_methods'] = fix_methods
                    entry['batch_id'] = batch_id
                    entry['jsonname'] = jsonname
                    if instruction_records:
                        if 'modified_title' not in entry:
                            entry['modified_title'] = []
                        entry['modified_title'].extend(instruction_records)
                    if entry['title'] + '$$' + str(entry['fix_methods']) + "+" + str(entry['batch_id']) in sorted(
                            [i['title'] + '$$' + str(i['fix_methods']) + "+" + str(i['batch_id']) for i in
                             aggregated_data]):
                        # TODO: Fix the bug
                        logger.error(entry['title'] + '\n' + str(entry['fix_methods']) + "\n" + str(entry['batch_id']))
                        break
                    flow_ins = WebAgentFlow(entry)
                    # for step in flow_ins.steps:
                    #     step.marked_screenshot =
                    aggregated_data.append(entry)
                    break
        if skip_instruction:
            logger.warning(f"[SKIPPED] {instruction}")
            continue
    return aggregated_data


def main():
    # 配置文件路径
    csv_path = Path(
        "/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/modification/20250527/QC_WebAgent_任务总表_数据修正汇总表.csv")  # CSV 文件路径
    json_dir = Path("/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/json_all")  # JSON 文件夹路径
    # actiontodo_name = ["质检平台-拉框"]  # 目标 ActionTodo
    actiontodo_name = None
    exclude_actiontodo_names = ['未知：需要帮助', '重新标注流程', '']
    allow_multiple_todo_name = True
    target_batch = None
    base_exclude_all = Path("/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/modification/20250603/delivered")
    exclude_entries_jsons=[Path(i) for i in glob.glob(str(base_exclude_all/'*.json'))]
    # 是否允许多个 ActionTodo 匹配

    # 获取所有 JSON 文件路径
    json_paths = list(json_dir.glob("*.json"))

    # 先加载所有 JSON 文件，将其按 instruction 聚合
    instruction_map = load_instructions_and_json(json_paths)

    # 获取聚合后的结果
    results = group_by_actiontodo_and_instructions(csv_path,
                                                   instruction_map,
                                                   target_actiontodo_names=actiontodo_name,
                                                   exclude_actiontodo_names=exclude_actiontodo_names,
                                                   allow_multiple_todo_name=allow_multiple_todo_name,
                                                   target_batch=target_batch,
                                                   exclude_entries_jsons=exclude_entries_jsons)
    # output_string = '_'.join(target_batch)
    # 输出结果到文件
    print(len(set([i['id'] for i in results])))
    output_dir = Path("/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/modification/20250604")
    output_dir.mkdir(parents=True, exist_ok=True)

    chunk_size = 30
    total_chunks = math.ceil(len(results) / chunk_size)

    # for idx in range(total_chunks):
    #     chunk = results[idx * chunk_size:(idx + 1) * chunk_size]
    #     output_path = output_dir / f"all_fix_{idx + 1}.json"
    #     with open(output_path, 'w', encoding='utf-8') as f:
    #         json.dump(chunk, f, ensure_ascii=False, indent=4)
    #
    #     log_path = output_dir / f"all_fix_log_{idx + 1}.json"
    #     with open(log_path, 'w', encoding='utf-8') as f:
    #         json.dump(
    #             sorted([i['title'] + '\n' + str(i['fix_methods']) + "\n" + str(i['batch_id']) for i in chunk]),
    #             f, ensure_ascii=False, indent=4
    #         )
    #
    # print(f"聚合结果已保存为 {total_chunks} 组，每组最多 {chunk_size} 条，共 {len(results)} 条记录")

if __name__ == "__main__":
    main()
