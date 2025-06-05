from modules.webagent_data_utils import WebAgentFlow
import json

json_path = "/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/modification/20250601/processedpreprocessed_ig_200_fix_20250527_094034.json"

with open(json_path, 'r') as f:
    data = json.load(f)

for flow in data:
    flow_ins = WebAgentFlow(flow)
    for step in flow_ins.steps:
        if step.recrop_rect:
            print(step.adjusted_rect)
            print("H")