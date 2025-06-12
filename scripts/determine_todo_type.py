import glob
import json

from modules.webagent_data_utils import WebAgentFlow


all_remake_jsons = glob.glob("/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/modification/20250609/check_remake_jsons/*.json")

remake_json_ids = []

for j in all_remake_jsons:
    with open(j, 'r') as f:
        d = json.load(f)
    remake_json_ids.extend([WebAgentFlow(i).id for i in d])

all_fix_methods = glob.glob("/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/modification/20250609/todo_all_todo/all_fix_*.json")
all_fix_methods_map = {}
for j in all_fix_methods:
    with open(j, 'r') as f:
        d = json.load(f)
    for i in d:
        all_fix_methods_map[WebAgentFlow(i).title] = WebAgentFlow(i)._flow_dict['fix_methods']

summary = {}
with open("/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/json_all_20250609/0_SUMMARY_TODO_BY_TITLE.json", 'r') as f:
    data = json.load(f)

path = "nonimg_flow_ids.json"
with open(path, 'r') as f:
    no_img_flow_ids = json.load(f)

for i in data:
    flow_ins = WebAgentFlow(i)
    if flow_ins.id not in summary:
        summary[flow_ins.id] = []
    if flow_ins.id in remake_json_ids:
        summary[flow_ins.id].append("REMAKE")
        continue
    if flow_ins.id in no_img_flow_ids:
        summary[flow_ins.id].append('NO_IMG')
    if flow_ins.title in all_fix_methods_map:
        # print(all_fix_methods_map[flow_ins.title])
        summary[flow_ins.id].extend(all_fix_methods_map[flow_ins.title])

# print(len([i for i in summary if summary[i]]))
# print(len(summary.keys()))
with open('todo_type_summary.json', 'w') as f:
    json.dump(summary, f, indent=4, ensure_ascii=False)

todo_entries = []

id_inst_map = {WebAgentFlow(i).id: i for i in data}

for entry in summary:
    skip = False
    for exclude in ['REMAKE', '后台批量修改（截图时机）', 'NO_IMG']:
        if exclude in summary[entry]:
            print(exclude)
            skip = True
            break
    if skip:
        continue
    todo_entries.append(id_inst_map[entry])
print(len(todo_entries))
chunk_size = 30
# 拆分成多个小文件
for i in range(0, len(todo_entries), chunk_size):
    chunk = todo_entries[i:i + chunk_size]
    chunk_index = i // chunk_size + 1
    output_path = f'given_todo_type_{chunk_index}.json'
    with open(output_path, 'w', encoding='utf-8') as out_f:
        json.dump(chunk, out_f, ensure_ascii=False, indent=2)
    print(f'Saved: {output_path}')