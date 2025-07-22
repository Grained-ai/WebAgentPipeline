import glob
from pathlib import Path
from modules.webagent_data_utils import WebAgentFlow, WebAgentStep
import json

jsons_all_path = Path("/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/all_delivered/true_delivery_17524797")

jsons = glob.glob(str(jsons_all_path / '*.json'))

total = 0

all_steps = []

for json_file in jsons:
    with open(json_file, 'r') as f:
        data = json.load(f)
    for flow_content in data:
        flow_ins = WebAgentFlow(flow_content)
        for step in flow_ins.steps:
            total += 1

print(total)