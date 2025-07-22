import glob
from pathlib import Path
from modules.webagent_data_utils import WebAgentFlow, WebAgentStep
import json
from loguru import logger

jsons_all_path = Path(
    "/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/all_delivered/true_delivery_17524797")

jsons = glob.glob(str(jsons_all_path / '*.json'))


def check_if_no_bbox(flow_ins: WebAgentFlow):
    for idx, step in enumerate(flow_ins.steps):
        if step.type not in ['press_enter', 'back', 'cache', 'paste', 'end',
                             'launchApp'] and step.title.lower() not in [
            'end']:
            if not step.adjusted_rect and not step.recrop_rect:
                logger.warning(f"{flow_ins.id} Missing Rect: Step {idx}. {step.title}. ")
                return True


def check_step_if_no_bbox(step_ins: WebAgentStep):
    if step_ins.type not in ['press_enter', 'back', 'cache', 'paste', 'end',
                             'launchApp'] and step.title.lower() not in [
        'end']:
        if not step_ins.adjusted_rect and not step_ins.recrop_rect and not step_ins._step_dict.get('recrop_rect'):
            logger.warning(f"{flow_ins.id} Missing Rect: Step {step_ins.id}. {step_ins.title}. ")
            return True


total = 0

all_steps = []
import pandas as pd

for json_file in jsons:
    with open(json_file, 'r') as f:
        data = json.load(f)
    for flow_content in data:
        flow_ins = WebAgentFlow(flow_content)
        for idx, step in enumerate(flow_ins.steps):
            if check_step_if_no_bbox(step):
                all_steps.append({'json_name': Path(json_file).name,
                                  'flow_id': flow_ins.id,
                                  'flow': flow_ins.title,
                                  'step_id': idx + 1,
                                  'step': step.title})
print(len(all_steps))

# 转换为 DataFrame
df = pd.DataFrame(all_steps)

# 保存为 Excel 文件
output_path = 'steps_without_bbox_20250714.xlsx'
df.to_excel(output_path, index=False)

print(f"保存成功: {output_path}")
