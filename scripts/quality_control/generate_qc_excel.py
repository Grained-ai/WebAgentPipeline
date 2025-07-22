import os
from pathlib import Path
import json
from loguru import logger
from modules.webagent_data_utils import WebAgentFlow
import pandas as pd
file_path = Path("/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/all_modification/modification/20250708/remove_delete_steps_recheck_skip_end_modify_title_remove_is_remake_remove_validation_remove_redo_parent_17519874")

json_paths = file_path.glob('*.json')

out = []
for json_path in json_paths:
    with open(json_path, 'r') as f:
        data = json.load(f)
    for d in data:
        flow_ins = WebAgentFlow(d)
        out.append({'instruction_id': flow_ins.id,
                    'instruction': flow_ins.title,
                    'json_name': json_path.name})
print(len(out))
# 创建 DataFrame
df = pd.DataFrame(out)

# 指定输出文件名
output_xlsx = file_path / "instruction_summary.xlsx"

# 将 DataFrame 写入 Excel，所有列设为文本格式，防止公式解析
with pd.ExcelWriter(output_xlsx, engine='openpyxl') as writer:
    df.to_excel(writer, index=False, sheet_name='summary')

logger.success(f"Excel file saved to {output_xlsx}")


