from pathlib import Path
from modules.webagent_data_utils import WebAgentFlow
import json
import pandas as pd

delivered = Path("/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/all_delivered/true_delivery_17524797")

json_paths = delivered.glob('*.json')
out = []
for json_path in json_paths:
    with open(json_path, 'r') as f:
        data = json.load(f)
    for d in data:
        flow_ins = WebAgentFlow(d)
        out.append({'flow_id': flow_ins.id,
                    'flow_title': flow_ins.title,
                    'json_name': json_path.name})

df = pd.DataFrame(out)

# 保存为 Excel 文件
output_path = 'final_deliver_20250714.xlsx'
df.to_excel(output_path, index=False)

print(f"保存成功: {output_path}")
