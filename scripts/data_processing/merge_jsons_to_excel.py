from pathlib import Path
import json

import tqdm
from modules.webagent_data_utils import WebAgentFlow

all_json_path = "/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/all_modification/modification/20250722/add_batch"
jsons = Path(all_json_path).glob("*.json")
print(jsons)

data = []
for _json in tqdm.tqdm(jsons):
    with open(_json, 'r') as f:
        d = json.load(f)

    for _d in d:
        ins = WebAgentFlow(_d)
        data.append({'instruction': ins.title,
                    'batch id': "makeup_56",
                    'json name': _json.name})

import pandas as pd

# 转成 DataFrame
df = pd.DataFrame(data)

# 导出到 Excel
output_path = "/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/all_modification/modification/20250722/add_batch_summary.xlsx"
df.to_excel(output_path, index=False)

print(f"✅ 导出成功：{output_path}")