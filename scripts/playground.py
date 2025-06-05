# from modules.llm_utils.translate_instruction import translate_step_title, enrich_step_title
#
# res = enrich_step_title(
#     "Click Local'\n'Extra Wide Big Bum Bike Saddle Seat Bicycle Gel Pad Soft Comfort For Bicycle UK",
#     '/Users/anthonyf/projects/grainedAI/WebAgentPipeline/src/sample_2_major_error/frames_marked/zGZa7D8dcPz19rH9KERpW_marked.jpeg')
# print(res)

# from modules.llm_utils.check_if_goto_instruction import check_if_goto_instruction
#
# todo = 'In the website "https://shop.app/", visit the store named "Fashion Nova" and add the first best selling product to cart.'
# todo= 'Set the trip preferences as tent, electric site, and water hookup amenities in the account.'
# todo = "Help me find newborn diapers on Target priced between $50 and $100, I don't mind paying a little more for comfort."
# todo = 'Quote the second article from the "Latest News" section on the CNBC website.'
# todo = '- Task 1: "Find me the top-rated hotels on kayak.com for family. I want to check their reviews to find the best options for my next trip."'
# res = check_if_goto_instruction(todo)
# print(res)

from modules.media_utils.image_ops import mark_redo_bbox, mark_click_position
from PIL import Image

from scripts.merge_json_results import flow_ins

image_path = "/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/modification/20250601/fn3pxAh8Y4F0ttLPNyNCD_marked.jpeg"
annotations = [
    {
        "type": "rect",
        "x": 463,
        "y": 462.21875,
        "width": 379,
        "height": 52,
        "xRatio": 0.22421307506053267,
        "yRatio": 0.30409128289473686,
        "widthRatio": 0.18353510895883776,
        "heightRatio": 0.034210526315789476
    }
]
import cv2
# 加载图像
# image = Image.open(image_path)
rect_info ={'left': 595, 'top': 679, 'right': 1063, 'bottom': 712}

# im = mark_redo_bbox(image, annotations)

image_path = "/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/modification/20250601/5oOg-zg_mYV31XJqOTCPi_marked.jpeg"

json_path = '/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/modification/20250604/all_fix_2.json'
from modules.webagent_data_utils import WebAgentFlow
from modules.instruction_level_modification import merge_consecutive_scrolls
from modules.instruction_level_check import check_consecutive_scrolls, check_if_wrong_step_type
import json
with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)
flow_inss = [WebAgentFlow(i) for i in data]
for flow_ins in flow_inss:
    # if flow_ins.id == 'MVJEVXrFN3tRe93mSdhbd':
        # res = check_if_wrong_step_type(flow_ins)
        # res.fix(flow_ins)
        # res = check_consecutive_scrolls(flow_ins)
        # a = [i.title for i in flow_ins.steps]
        # print(a)
        # ins = res.fix(flow_ins)
        # print([i.title for i in ins.steps])
    for step in flow_ins.steps:
        if step.id == '5oOg-zg_mYV31XJqOTCPi':
            print("HERE")
            image = cv2.imread(str(image_path))

            adujested_rect = step.adjusted_rect
            im = mark_click_position(image, x=0, y=0, rect=adujested_rect)
            cv2.imshow('dd', im)
            cv2.waitKey()

