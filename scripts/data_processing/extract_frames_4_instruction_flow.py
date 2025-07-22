from configs.configs import STORAGE_PATH
from modules.webagent_data_utils import WebAgentFlow
from modules.step_level_modification import extract_blank_frame, extract_blank_frame_webm, label_bbox
import json

def extract_frames_4_flow(flow: WebAgentFlow):
    for step in flow.steps:
        if not step.recording_id:
            continue
        extract_blank_frame(step, storage_path=STORAGE_PATH)
        label_bbox(step, storage_path=STORAGE_PATH)
        # extract_blank_frame_webm(step, storage_path=STORAGE_PATH)

if __name__ == "__main__":
    json_path = "/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/modification/20250529/38.json"
    with open(json_path, 'r') as f:
        data = json.load(f)
    print(type(data[0]))
    for flow_content in data:
        flow_ins = WebAgentFlow(flow_content)
        if flow_ins.id == '2GnWvNJy8gMf2GIsI1Tr3':
            extract_frames_4_flow(flow_ins)
