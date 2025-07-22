from pathlib import Path
from modules.webagent_data_utils import WebAgentFlow
import json
all_json_path = Path('/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/all_modification/modification/20250702/redo_150_finished')

unknown_jsons = all_json_path.glob('*.json')

submitted_jsons = Path('/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/all_delivered/all_delivered_20250702_before_merge_fix')
jsons_submitted = submitted_jsons.glob('*json')

from modules.flow_utils.flow_ops import json_to_flows, flows_to_excel

unknown_flows = json_to_flows(unknown_jsons)
submitted_flows = json_to_flows(jsons_submitted)

filtered_flows = []

submitted_flows_ids = [i.id for i in submitted_flows]

for unknown_flow in unknown_flows:
    if unknown_flow.id not in submitted_flows_ids:
        filtered_flows.append(unknown_flow)

flows_to_excel(filtered_flows, 'redo')