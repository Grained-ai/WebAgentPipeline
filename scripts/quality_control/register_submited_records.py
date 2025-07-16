import glob
from pathlib import Path
import json
import pandas as pd
from modules.webagent_data_utils import WebAgentFlow

all_delivered_path = "/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/all_delivered/all_delivered_20250625_before_merge_fix"
all_delivered_path = Path(all_delivered_path)

all_20250625_json = glob.glob(str(all_delivered_path / '*2025-06-24.json'))

# 数据存储
data = []

ids = []

for json_file in all_20250625_json:
    with open(json_file, 'r') as f:
        content = json.load(f)
        for ins_content in content:
            flow_ins = WebAgentFlow(ins_content)
            if flow_ins.id in ids:
                print(f"skip {flow_ins.id}")
                continue
            dp = {'instruction_id': flow_ins.id,
                  'instruction': flow_ins.title,
                  'json_name': Path(json_file).stem}
            data.append(dp)
            ids.append(flow_ins.id)

# 转为 DataFrame
df = pd.DataFrame(data)

# 保存 Excel 到当前运行目录
output_path = Path('./extracted_instructions.xlsx')
df.to_excel(output_path, index=False)
