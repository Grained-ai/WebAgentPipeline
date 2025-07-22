import glob
from pathlib import Path
import json

files = Path("/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/modification/all_delivered")
jsons = glob.glob(str(files/'*.json'))
print(len(jsons))
from modules.webagent_data_utils import WebAgentFlow
out = []
for i in jsons:
    with open(i, 'r') as f:
        data = json.load(f)
        flag = False
        for d in data:
            ins = WebAgentFlow(d)
            for step in ins.steps:
                if 'REMOVED' in step.title:
                    flag = True
                    break
        if not flag:
            out.append(i)
print(len(out))
new_out = []
for i in out:
    if '2025' in i:
        new_out.append('/var/www/html/submitjson/'+i.split('/')[-1])
print(' '.join(new_out))