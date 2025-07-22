import json
from pathlib import Path

import tqdm

from modules.webagent_data_utils import WebAgentFlow
import glob
from loguru import logger
all_good_preproess_empty_path = Path('/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/modification/20250603/modified_version_from_server')
jsons = [i for i in glob.glob(str(all_good_preproess_empty_path/'*.json')) if 'log' not in i]

step_mapping = {}
for j in tqdm.tqdm(jsons):
    with open(j, 'r') as f:
        data = json.load(f)
    for i in data:
        f_i = WebAgentFlow(i)
        step_mapping[f_i.id] = f_i

pre_sub_json_path = Path("/Users/anthonyf/projects/grainedAI/WebAgentPipeline/scripts")

jsons = [i for i in glob.glob(str(pre_sub_json_path/'*.json')) if 'log' not in i]

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
                if step.title != step_mapping[step.id].title:
                    logger.warning(f"{step.title}->{step_mapping[step.id].title}")
                    step.title = step_mapping[step.id].title
        processed_data.append(f_i.to_dict())
    with open(Path(j).name, 'w') as f:
        json.dump(processed_data, f, indent=4, ensure_ascii=False)