import json
from pathlib import Path

import tqdm

from modules.webagent_data_utils import WebAgentFlow
import glob
from loguru import logger
all_good_preproess_empty_path = Path('/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/modification/20250603/server_preprocess_v1_empty')
jsons = [i for i in glob.glob(str(all_good_preproess_empty_path/'*.json')) if 'log' not in i]

step_mapping = {}
for j in tqdm.tqdm(jsons):
    with open(j, 'r') as f:
        data = json.load(f)
    for i in data:
        f_i = WebAgentFlow(i)
        for step in f_i.steps:
            step_mapping[step.id] = step

pre_sub_json_path = Path("/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/modification/20250603/modified_version_from_server")

jsons = [i for i in glob.glob(str(pre_sub_json_path/'*.json')) if 'log' not in i]

apply_by_website = {}

for j in jsons:
    with open(j, 'r') as f:
        data = json.load(f)
    processed_data = []
    for i in data:
        f_i = WebAgentFlow(i)
        for step in f_i.steps:
            if step.id in step_mapping:
                if step.type != step_mapping[step.id].type:
                    logger.warning(f"{f_i.title} {step.title}: {step.type}->{step_mapping[step.id].type}")
                    step.type = step_mapping[step.id].type
                    step.title = step_mapping[step.id].title
        default_website_candi = [j for j in
                                 [i._step_dict.get("host") for i in f_i.steps]
                                 if j]
        default_website = default_website_candi[0] if default_website_candi else "UNKNOWN"
        # website = all_instructions[instruction][json_name].get('website', default_website)
        if len(default_website.split('.')) > 2:
            website = default_website.split('.')[1]
        elif len(default_website.split('.')) == 2:
            website = default_website.split('.')[0]
        else:
            website = "UNKNOWN"
        if website not in apply_by_website:
            apply_by_website[website] = []
        apply_by_website[website].append(f_i.to_dict())
        processed_data.append(f_i.to_dict())

all_count = 0

for key in apply_by_website:
    all_count += len(apply_by_website[key])
    with open(f"{key}.json", 'w') as f:
        json.dump(apply_by_website[key], f, ensure_ascii=False, indent=4)
    # with open(Path(j).name, 'w') as f:
    #     json.dump(processed_data, f, indent=4, ensure_ascii=False)
print(all_count)