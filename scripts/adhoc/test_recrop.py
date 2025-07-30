from modules.webagent_data_utils import WebAgentFlow
from pathlib import Path
import json

path = Path('/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/all_modification/modification/wsj_2025-07-14_part_1_bak.json')

with open(path, 'r') as f:
    d = json.load(f)

for _d in d:
    ins = WebAgentFlow(_d)
    print("HERE")
    for step in ins.steps:
        if step.type.lower() not in ['launchapp', 'press_enter', 'end'] or 'end' not in step.title.lower():
            print("HERE")
        else:
            print("HERE")

