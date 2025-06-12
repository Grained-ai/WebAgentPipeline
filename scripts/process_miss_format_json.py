from pathlib import Path
import json

from modules.webagent_data_utils import WebAgentFlow

file_path = '/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/modification/20250611/preprocessed_check_unknown_3_20250611_062134.json'
file_path = Path(file_path)

out = []

with open(file_path, 'r') as f:
    data = json.load(f)

for d in data:
    s = WebAgentFlow(d)
    out.append(s.to_dict())

with open(file_path.parent / str(file_path.stem + '_2.json'), 'w') as f:
    json.dump(out, f, indent=4, ensure_ascii=False)


