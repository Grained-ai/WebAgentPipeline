from modules.webagent_data_utils import WebAgentFlow
from modules.step_level_modification import extract_blank_frame, label_bbox, extract_blank_frame_webm, \
    extract_frame_at_timestamp
from modules.media_utils.image_ops import mark_click_position
from pathlib import Path
import json
import cv2

STORAGE_BASE = Path("/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/fix_wrong_frame")

with open('/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/fix_wrong_frame/fix_content.json', 'r') as f:
    data = json.load(f)

flow_ins = WebAgentFlow(flow_dict=data)
id = 'VLC1ZDVpE83UAvuqEmQdx'
for idx, step in enumerate(flow_ins.steps):
    if step.id == id:
        duration = (flow_ins.steps[idx+1].timestamp - step.timestamp)//15
        for candi, timestamp in enumerate(range(step.timestamp, flow_ins.steps[idx+1].timestamp, duration)):
            image_path = STORAGE_BASE / "debug.jpeg"
            marked_image_path = STORAGE_BASE / f"marked_debug_{candi}.jpeg"
            extract_frame_at_timestamp(
                STORAGE_BASE / str(step.recording_id + '.mp4'),
                timestamp_ms=step.timestamp+duration,
                output_image_path=image_path)
            frame = cv2.imread(str(image_path))
            # frame2 = mark_click_position(frame, None, None, step.adjusted_rect)
            # cv2.imwrite(marked_image_path, frame2)
