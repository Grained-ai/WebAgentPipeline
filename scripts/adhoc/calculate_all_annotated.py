from pathlib import Path
import json
from modules.webagent_data_utils import WebAgentFlow
jsons = Path("/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/all_delivered/all_delivered").rglob('*.json')
all_steps = 0
all_flows = 0
err_steps = 0
err_flows = 0

for j in jsons:
    with open(j, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for d in data:
        is_err = False
        ins = WebAgentFlow(d)
        for step in ins.steps:
            if step._step_dict.get('annotations') or step._step_dict.get('isremake') or step._step_dict.get('recrop_rect'):
                err_steps+=1
                is_err = True
            all_steps+=1

        if is_err:
            err_flows+=1
        all_flows+=1

print(err_steps, err_flows, all_steps, all_flows)
print(err_steps/all_steps)
print(err_flows/all_flows)