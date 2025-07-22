# import glob
# from pathlib import Path
# import json
#
# import tqdm
#
# from modules.webagent_data_utils import WebAgentFlow
#
# json_all = "/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/all_modification/modifyjson_20250610"
#
# all_jsons = list(Path(json_all).rglob('*.json'))
#
# all_is_remake_instructions = {}
#
# step_count = 0
# flow_count = 0
#
# for json_f in all_jsons:
#     with open(json_f, 'r') as f:
#         data = json.load(f)
#
#     for i in tqdm.tqdm(data):
#         flow_ins = WebAgentFlow(i)
#         for step in flow_ins.steps:
#             if step.is_remake or step.type in ['select', 'drag']:
#                 if flow_ins.id not in all_is_remake_instructions:
#                     all_is_remake_instructions[flow_ins.id] = {}
#                     flow_count += 1
#                 if step.id not in all_is_remake_instructions[flow_ins.id]:
#                     all_is_remake_instructions[flow_ins.id][step.id] = []
#                     step_count += 1
#                 all_is_remake_instructions[flow_ins.id][step.id].append({"instruction": flow_ins.title,
#                                                                          "step_instruction": step.title,
#                                                                          'step_id': step.id,
#                                                                          'step_href': step._step_dict.get('href'),
#                                                                          'web_element_path': step._step_dict.get(
#                                                                              "path")})
# print(step_count)
# print(flow_count)
# with open('all_is_remake_items.json', 'w') as f:
#     json.dump(all_is_remake_instructions, f, ensure_ascii=False, indent=4)
#
# with open(
#         "/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/json_all_20250609/0_SUMMARY_TODO_BY_TITLE.json",
#         'r') as f:
#     data = json.load(f)
#
# unknown_todo = []
#
# # for i in data:
# #     if i['id'] not in all_is_remake_instructions.keys():
# #         unknown_todo.append(i)
#
#
#
# with open('/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/all_delivered/all_delivered_20250610/A_SUMMARY_BY_TITLE.json', 'r') as f:
#     data2 = json.load(f)
#
# for i in data:
#     if i['id'] not in all_is_remake_instructions.keys() and i['title'] not in data2.keys():
#         unknown_todo.append(i)
# print(len(unknown_todo))
# with open('unknown_todo.json', 'w') as f:
#     json.dump(unknown_todo, f, indent=4, ensure_ascii=False)

# Extract is_remake from folder
from pathlib import Path
import json

from modules.webagent_data_utils import WebAgentFlow

folder_path = Path("/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/modification/20250626/extract_still_is_remake")
jsons = folder_path.rglob('*.json')

out = []
total = set()
for json_ in jsons:
    with open(json_, 'r') as f:
        data = json.load(f)
    for d in data:
        skip = False
        ins = WebAgentFlow(d)
        total.add(ins.id)
print(len(total))
#         for step in ins.steps:
#             if step.is_remake:
#                 out.append(d)
#                 skip = True
#                 break
#         if skip:
#             continue
# print(len(out))
# chunk_size = 30
# # 拆分成多个小文件
# for i in range(0, len(out), chunk_size):
#     chunk = out[i:i + chunk_size]
#     chunk_index = i // chunk_size + 1
#     output_path = f'redo_is_remake_{chunk_index}.json'
#     with open(output_path, 'w', encoding='utf-8') as out_f:
#         json.dump(chunk, out_f, ensure_ascii=False, indent=2)
#     print(f'Saved: {output_path}')