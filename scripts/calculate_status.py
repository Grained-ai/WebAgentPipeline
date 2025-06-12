import tqdm
from pathlib import Path
from modules.webagent_data_utils import WebAgentFlow
import glob
import json
from loguru import logger

jsno_base = Path('/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/all_delivered/all_delivered_20250610/')
jsons = [i for i in glob.glob(str(jsno_base/'*.json')) if "SUMMARY" not in i]

all_instruction_by_id = {}

for j in tqdm.tqdm(jsons):
    with open(j, 'r') as f:
        data = json.load(f)
    for i in data:
        f_i = WebAgentFlow(i)
        if f_i.id not in all_instruction_by_id:
            all_instruction_by_id[f_i.id] = {}
        if f_i.title not in all_instruction_by_id[f_i.id]:
            all_instruction_by_id[f_i.id][f_i.title] = []

        all_instruction_by_id[f_i.id][f_i.title].append(Path(j).name)

all_instructions_by_title = {}

for j in tqdm.tqdm(jsons):
    with open(j, 'r') as f:
        data = json.load(f)
    for i in data:
        f_i = WebAgentFlow(i)

        if f_i.title not in all_instructions_by_title:
            all_instructions_by_title[f_i.title]= {}

        if f_i.id not in all_instructions_by_title[f_i.title]:
            all_instructions_by_title[f_i.title][f_i.id] = []

        all_instructions_by_title[f_i.title][f_i.id].append(Path(j).name)

with open(jsno_base/'A_SUMMARY_BY_ID.json', 'w') as f:
    json.dump(all_instruction_by_id, f, ensure_ascii=False, indent=4)

with open(jsno_base/'A_SUMMARY_BY_TITLE.json', 'w') as f:
    json.dump(all_instructions_by_title, f, ensure_ascii=False, indent=4)

print(len(all_instruction_by_id.keys()))
print(len(all_instructions_by_title.keys()))

## SUMMARIZE ALL WE HAVE
all_existing = Path("/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/json_all_20250609")
jsons = [i for i in glob.glob(str(all_existing/'*.json')) if "SUMMARY" not in i]

todo_by_id = []
todo_by_title = []

total = []

for j in tqdm.tqdm(jsons):
    with open(j, 'r') as f:
        data = json.load(f)
    for i in data:
        f_i = WebAgentFlow(i)
        if f_i.id not in all_instruction_by_id:
            todo_by_id.append(i)
        if f_i.title not in all_instructions_by_title:
            todo_by_title.append(i)

with open(all_existing/'0_SUMMARY_TODO_BY_TITLE.json', 'w') as f:
    json.dump(todo_by_title, f, indent=4, ensure_ascii=False)

print(len(todo_by_title))

# GET ALL IS_REMAKE


# chunk_size = 30
# # 拆分成多个小文件
# for i in range(0, len(all_instructions), chunk_size):
#     chunk = all_instructions[i:i + chunk_size]
#     chunk_index = i // chunk_size + 1
#     output_path = f'check_fix_{chunk_index}.json'
#     with open(output_path, 'w', encoding='utf-8') as out_f:
#         json.dump(chunk, out_f, ensure_ascii=False, indent=2)
#     print(f'Saved: {output_path}')