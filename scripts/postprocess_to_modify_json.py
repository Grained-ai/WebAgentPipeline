import json
from pathlib import Path
# from modules.webagent_data_utils import WebAgentStep, WebAgentFlow
import argparse
from loguru import logger

def modification(json_path: Path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    log_json = json_path.parent/str(json_path.stem+"_log.json")
    with open(log_json, 'r', encoding='utf-8') as f:
        log_data = json.load(f)

    error_step_id = [i['step_id'] for i in log_data['failure_details']]

    modified_outs = []

    for flow_content in data:
        # flow = WebAgentFlow(flow_content)
        # skip_flow = False
        # for step in flow_content['steps']:
        #     if step['id'] in error_step_id:
        #         skip_flow = True
        #         break
        # if skip_flow:
        #     continue
        fix_method_string = '\n'.join(flow_content['fix_methods'])
        flow_content['title'] = flow_content['title']+f'\n{fix_method_string}'
        modified_outs.append(flow_content)

    finished_path = json_path.parent/str('processed'+json_path.name)
    with open(finished_path, 'w', encoding='utf-8') as f:
        json.dump(modified_outs, f, ensure_ascii=False, indent=4)
    logger.success(f"{len(data)}->{len(modified_outs)}. {finished_path}")

def main():
    parser = argparse.ArgumentParser(description="AutoQC Pipeline: Process JSON files to find issues.")

    # 2. 添加命令行参数
    parser.add_argument(
        'json_path',
        type=str,
        help="Path to the JSON file to be processed"
    )
    args = parser.parse_args()
    json_path = Path(args.json_path)
    modification(json_path)

if __name__ == "__main__":
    main()