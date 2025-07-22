import json

from modules.webagent_data_utils import WebAgentFlow
from pathlib import Path

json_base = Path("/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/all_modification/modification/20250624/all_fix")

target_base = json_base.rglob("preprocessed_好运来_K*.json")

def get_modified_flow_count(json_path):
    with open(json_path, 'r') as f:
        data = json.load(f)

    flow = []
    not_modifed = []
    for f_content in data:
        ins = WebAgentFlow(f_content)
        modified = False
        for step in ins.steps:
            if '[]' in step.title:
                modified = True
                break

            if '[is_remake]' in step.title:
                modified = True
                break

            if step.recrop_rect:
                modified = True
                break

            if step.deleted and step.type.lower() not in ['launchapp']:
                modified = True
                break
        if modified:
            flow.append(ins)
            continue
        else:
            not_modifed.append(ins)

    return flow, not_modifed

sum_flows = []
sum_not_flow = []
for json_p in target_base:
    print(json_p)
    m_flows, n_m_flows = get_modified_flow_count(json_p)
    sum_flows.extend(m_flows)
    sum_not_flow.extend(n_m_flows)

print(len(sum_flows))
print(len(sum_not_flow))