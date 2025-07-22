import glob
import json

all_jsons = "/Users/anthonyf/projects/grainedAI/WebAgentPipeline/src/batches/20250521"
from pathlib import Path

all_jsons = Path(all_jsons)
all_js = glob.glob(str(all_jsons/'*.json'))
summary = []

for j in all_js:
    with open(j, 'r') as f:
        data = json.load(f)

    summary.extend(data)

print(len(summary))
print(sum([len(i['steps']) for i in summary]))