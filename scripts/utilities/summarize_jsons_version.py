from configs.configs import ALL_JSON_STORAGE_PATH
from modules.webagent_data_utils import WebAgentFlow
from pathlib import Path
from glob import glob
import json
from loguru import logger
import re

jsons = glob(str(Path(ALL_JSON_STORAGE_PATH) / '*.json'))

all_instructions = {}

for j in jsons:
    json_name = Path(j).stem
    with open(j, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for ins in data:
        flow_ins = WebAgentFlow(ins)
        flow_ins.title = flow_ins.title.strip().replace("  ", ' ')
        if 'preprocessed' in json_name:
            match = re.search(r'[\u4e00-\u9fff]', flow_ins.title)
            if match:
                flow_ins.title = flow_ins.title[:match.start()].strip()
            else:
                flow_ins.title = flow_ins.title.strip()
        if flow_ins.title not in all_instructions:
            all_instructions[flow_ins.title] = {}
        all_instructions[flow_ins.title][json_name] = {"id": flow_ins.id, "content": flow_ins.to_dict()}

import csv

# 假设你已经把内容保存成 data.csv 文件
with open('/Users/anthonyf/projects/grainedAI/WebAgentPipeline/scripts/QC_WebAgent_任务总表_交付表.csv', newline='',
          encoding='utf-8-sig') as csvfile:
    reader = csv.DictReader(csvfile)

    for row in reader:
        instruction = row['instruction'].strip()
        instruction = instruction.replace("  ", ' ')
        json_name = row['json_name'].strip()
        batch_id = row['batch id'].strip()
        is_delivered = row['is_delivered'].strip()
        website = row['website'].strip()
        json_name = json_name.split('.json')[0]
        all_instructions[instruction][json_name]['batch_id'] = batch_id
        all_instructions[instruction][json_name]['is_delivered'] = is_delivered
        all_instructions[instruction][json_name]['website'] = website

skipped_count = 0
classified_by_website = {}
modified_count = []
for instruction in all_instructions:
    is_ddd = False
    for json_name in all_instructions[instruction]:
        if all_instructions[instruction][json_name].get('is_delivered'):
            default_website_candi = [j for j in [i.get("host") for i in all_instructions[instruction][json_name]['content']['steps']] if j]
            default_website = default_website_candi[0] if default_website_candi else "UNKNOWN"
            # website = all_instructions[instruction][json_name].get('website', default_website)
            if len(default_website.split('.')) > 2:
                website = default_website.split('.')[1]
            elif len(default_website.split('.')) == 2:
                website = default_website.split('.')[0]
            else:
                all_instructions[instruction][json_name].get('website', default_website)

            # if website not in classified_by_website:
            #     classified_by_website[website] = []
            # classified_by_website[website].append(all_instructions[instruction][json_name]['content'])
            is_ddd = True
            break
    if is_ddd:
        logger.info("Already delivered")
        skipped_count += 1
        continue

    subbed = False
    instruction_content = None
    website = None
    json_name = None
    for json_name in all_instructions[instruction].keys():
        if 'preprocessed' in json_name:
            continue
        if "[redo" in json_name:
            subbed = True
            break
        if "w_check"  in json_name:
            break
    logger.debug(f"Selected {json_name}")
    instruction_content = all_instructions[instruction][json_name]['content']
    default_website_candi = [j for j in
                             [i.get("host") for i in all_instructions[instruction][json_name]['content']['steps']]
                             if j]
    default_website = default_website_candi[0] if default_website_candi else "UNKNOWN"
    if len(default_website.split('.')) > 2:
        website = default_website.split('.')[1]
    elif len(default_website.split('.')) == 2:
        website = default_website.split('.')[0]
    else:
        all_instructions[instruction][json_name].get('website', default_website)


    if not website:
        print("HERE")

    step_recrop = {}
    step_remake = {}
    step_remove = {}
    step_title = {}
    for json_name in all_instructions[instruction]:
        flow_i = WebAgentFlow(all_instructions[instruction][json_name]['content'])
        for step in flow_i.steps:
            if step.recrop_rect:
                step_recrop[step.id] = step.recrop_rect
            if step.is_remake:
                step_remake[step.id] = True
            if step.deleted_by_qc:
                step_remove[step.id] = step.deleted_by_qc
            step_title[step.id] = step.title

    if not instruction_content:
        continue
    flow_in = WebAgentFlow(instruction_content)
    for step in flow_in.steps:
        if step.id in step_recrop:
            logger.success('Step recrop substituted.')
            step.recrop_rect = step_recrop[step.id]
            subbed = True
        if step.id in step_remake:
            logger.success('Step recrop substituted.')
            step.is_remake = step_remake[step.id]
            subbed = True
        if step.id in step_remove:
            logger.success('Step recrop substituted.')
            step.deleted = True
            subbed = True
        if step.id in step_title:
            logger.success('Step recrop substituted.')
            step.title = step_title[step.id]
            if step.type == 'launchApp' and step.deleted and '[REMOVED]' not in step.title:
                step.deleted = False
                step.title = ''
            subbed = True
    if subbed:
        skip = False
        for step in flow_in.steps:
            if step.is_remake:
                skip = True
                break
            if step.type =='select':
                skip = True
                break
        if skip:
            continue
        modified_count.append(flow_in.id)
        # default_website_candi = [j for j in [i._step_dict.get("host") for i in flow_in.steps if j]]
        # default_website = default_website_candi[0] if default_website_candi else "UNKNOWN"
        # website = all_instructions[instruction][json_name].get('website', default_website)

        if website not in classified_by_website:
            classified_by_website[website] = []
        classified_by_website[website].append(flow_in.to_dict())
    else:
        logger.error('Not yet finished.')
logger.error(skipped_count)
all_count = 0
modified_classified_by_website = {}
for i in classified_by_website:
    if i in ['UNKNOWN', '']:
        if "UNKNOWN" not in modified_classified_by_website:
            modified_classified_by_website["UNKNOWN"] = []

        modified_classified_by_website["UNKNOWN"].extend(classified_by_website[i])
    else:
        if i not in modified_classified_by_website:
            modified_classified_by_website[i] = []
        modified_classified_by_website[i].extend(classified_by_website[i])

for key in modified_classified_by_website:
    all_count += len(modified_classified_by_website[key])
    with open(f"{key}.json", 'w') as f:
        json.dump(modified_classified_by_website[key], f, ensure_ascii=False, indent=4)
print(all_count)
# # with open('all_instructions.json', 'w', encoding='utf-8') as f:
# #     json.dump(all_instructions, f, ensure_ascii=False, indent=4)
#
# chunk_size = 30
# import os
#
# data = modified_classified_by_website['UNKNOWN']
# # 拆分成多个小文件
# for i in range(0, len(data), chunk_size):
#     chunk = data[i:i + chunk_size]
#     chunk_index = i // chunk_size + 1
#     output_path = f'UNKNOWN_{chunk_index}.json'
#     with open(output_path, 'w', encoding='utf-8') as out_f:
#         json.dump(chunk, out_f, ensure_ascii=False, indent=2)
#     print(f'Saved: {output_path}')