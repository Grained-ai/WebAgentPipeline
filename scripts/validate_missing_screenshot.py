import glob
from pathlib import Path

import tqdm

image_base = "/var/www/html/storage/frames_raw"

to_check_json = "0_SUMMARY_TODO_BY_TITLE.json"

import json

with open(to_check_json, 'r') as f:
    data = json.load(f)

to_determine = []

missing_image_steps = []
missing_image_instruction = set()
for ins in tqdm.tqdm(data):
    flow = ins
    for step in flow['steps']:
        if step['type'].lower() == 'launchapp':
            continue
        res = glob.glob(str(Path(image_base)/f'{step['id']}*.jpeg'))
        if not res:
            missing_image_steps.append(step['id'])
            missing_image_instruction.add(flow['id'])

print(len(missing_image_instruction))

with open('validate_missing_result.json', 'w') as f:
    json.dump(list(missing_image_instruction), f, ensure_ascii=False, indent=4)

# import json
#
# json_1 = "/Users/anthonyf/projects/grainedAI/WebAgentPipeline/scripts/validate_missing_result2.json"
# json_2 = "/Users/anthonyf/projects/grainedAI/WebAgentPipeline/scripts/validate_missing_result.json"
#
# with open(json_1, 'r') as f:
#     data = json.load(f)
#
# with open(json_2, 'r') as f:
#     data2 = json.load(f)
#
# out = set(data).intersection(set(data2))
# print(len(out))