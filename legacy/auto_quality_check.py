import traceback
from pathlib import Path

import tqdm
from loguru import logger
import json
import random
import string
import cv2
import os
from PIL import Image, ImageDraw
import numpy as np
from modules.media_utils.video_ops import convert_webm_to_mp4, get_video_duration_ms

DEFAULT_VIEWPORT = {'width': 1050, 'height': 759}
FLOW_PROCESSES = [
    'flow_process_merge_consecutive_scrolls',
    'flow_process_check_and_add_end_step'
]

STEP_PROCESSES = [
    'step_process_extract_frame',
    'step_process_label_bbox',
    'step_process_step_chinese2english',
    'step_process_step_type_mapping',
    'step_process_update_imgSave_to_marked_screenshot'
]


class QCException(Exception):
    class FlowException(Exception):
        pass

    class StepException(Exception):
        pass


class JSONAutoQC:
    def __init__(self, json_path, legacy_image_dir=None):
        self.legacy_image_dir = legacy_image_dir
        self.storage_path = Path(json_path).parent
        self.json_path = Path(json_path)

        os.makedirs(self.storage_path, exist_ok=True)

    @staticmethod
    def merge_scroll_group_in_place(scroll_group):
        """合并scroll操作组，仅保留最后一个scroll，并修改其scrollDistance与scrollDirection"""
        if len(scroll_group) == 0:
            return None
        if len(scroll_group) == 1:
            return scroll_group[0]

        first = scroll_group[0]
        last = scroll_group[-1]

        # 计算合并后的 scrollDistance
        if first.get("scrollDirection") == "down":  # 向下滚动起始点为 终点-向下距离
            first_diatance = first.get("scrollPosition", 0) - first.get("scrollDistance", 0)
            if first_diatance < 0:
                first_diatance = 0
        else:  # 向上滚动起始点为 终点+向上距离
            if first.get("scrollPosition") == 0:  # 在顶部向上滚动无效果
                first_diatance = 0
            else:
                first_diatance = first.get("scrollPosition", 0) + first.get("scrollDistance", 0)
        distance = abs(last.get("scrollPosition", 0) - first_diatance)
        # 统计总滚动距离按方向划分
        direction_totals = {"up": 0, "down": 0}
        for s in scroll_group:
            dir = s.get("scrollDirection", "down")
            dist = abs(s.get("scrollDistance", 0))
            if dir == "up" and s.get("scrollPosition") == 0:
                dist = 0
            direction_totals[dir] += dist

        merged_direction = "down" if direction_totals["down"] >= direction_totals["up"] else "up"
        # 检查是否需要更新 title
        original_direction = last.get("scrollDirection")
        if original_direction != merged_direction:
            if merged_direction == "down":
                last["title"] = "向下滚动"
            else:
                last["title"] = "向上滚动"
        # 直接修改最后一个 scroll 操作
        last["scrollDirection"] = merged_direction
        last["scrollDistance"] = distance
        logger.success(
            f"合并了 {len(scroll_group)} 个scroll操作 -> scrollDirection: {merged_direction}, scrollDistance: {distance}")
        return last

    @staticmethod
    def generate_random_id(length):
        """生成指定长度的随机ID"""
        return ''.join(random.choices(string.ascii_letters + string.digits + '-_', k=length))

    @staticmethod
    def mark_click_position(image, x, y, rect=None, radius=10):
        """在图片上标记点击位置和元素区域"""
        # 获取并打印图片尺寸
        height, width = image.shape[:2]
        logger.info(f"截图尺寸: {width}x{height} 像素")

        # 转换OpenCV图片为PIL图片
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(image_rgb)
        draw = ImageDraw.Draw(pil_image)
        if x and y:
            # 绘制点击标记（十字线和圆圈）
            draw.ellipse([x - radius, y - radius, x + radius, y + radius],
                         outline='red', width=2)
            draw.line([(x - radius, y), (x + radius, y)], fill='red', width=2)
            draw.line([(x, y - radius), (x, y + radius)], fill='red', width=2)

        # 如果提供了rect信息，绘制矩形框
        if rect:
            # 使用rect中的坐标信息绘制矩形
            left = rect['left']
            top = rect['top']
            right = rect['right']
            bottom = rect['bottom']
            # 使用半透明的红色绘制矩形
            overlay = Image.new('RGBA', pil_image.size, (0, 0, 0, 0))
            draw_overlay = ImageDraw.Draw(overlay)
            draw_overlay.rectangle([left, top, right, bottom],
                                   outline='red',
                                   width=2,
                                   fill=(255, 0, 0, 30))  # 半透明红色填充
            # 将半透明层合并到原图
            pil_image = Image.alpha_composite(pil_image.convert('RGBA'), overlay)

        # 转换回OpenCV格式
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGBA2BGR)

    def step_check_if_chinese(self, step_content):
        step_id = step_content.get("id")
        step_type = step_content.get('type')
        if not step_type:
            raise QCException.StepException(f'Step {step_id} missing type.')


    def step_process_step_chinese2english(self, step_content):
        step_id = step_content.get("id")
        step_type = step_content.get('type')
        screenshot_path = step_content.get('screenshot')
        current_title = step_content.get('title')
        prev_title = step_content.get('title')

        if "局部" in current_title:
            if current_title == '局部向上滚动':
                current_title = 'Scroll up the boxed part'
            elif current_title == '局部向下滚动':
                current_title = 'Scroll down the boxed part'
            else:
                logger.warning(f"Unknown 局部 step title. {current_title}")
            logger.warning(f'[Update]: {prev_title} -> {current_title}')

        if '滚动' in current_title:
            if current_title == '向上滚动':
                current_title = 'Scroll up the whole screen'
            elif current_title == '向下滚动':
                current_title = 'Scroll down the whole screen'
            else:
                logger.warning(f"Unknown 滚动 step title. {current_title}")
            logger.warning(f'[Update]: {prev_title} -> {current_title}')

        if any('\u4e00' <= ch <= '\u9fff' for ch in current_title):
            logger.warning("Will do Chinese2English")
            current_title = f"{step_type.capitalize()} {step_content.get('value') if step_content.get('value') else current_title[2:].strip()}"
            logger.warning(f'[Update]: {prev_title} -> {current_title}')

        step_content['title'] = current_title
        return step_content

    def step_process_update_imgSave_to_marked_screenshot(self, step_content):
        marked_screenshot_rel_path = step_content.get("marked_screenshot")
        if marked_screenshot_rel_path:
            marked_screenshot_path = self.storage_path/marked_screenshot_rel_path
            if marked_screenshot_path.exists():
                step_content['imgSave'] = "http://3.145.59.104/submitjson/"+marked_screenshot_rel_path
                logger.success(f"[ImgSave Updated] -> {step_content['imgSave']}")
        return step_content

    def flow_process_check_and_add_end_step(self, flow_content):
        if 'steps' not in flow_content or len(flow_content['steps']) == 0:
            raise QCException.FlowException(
                f"No steps in flow: {flow_content.get('id')}. Title: {flow_content.get('title')}")

        last_step = flow_content['steps'][-1]
        if last_step.get('title', '').upper() != 'END':
            logger.warning(f"Need to add END step for {flow_content.get('id')}.")
            recording_id = None
            for step in flow_content['steps']:
                if 'recordingId' in step:
                    recording_id = step['recordingId']
                    break

            if recording_id:
                # 构建视频文件路径
                webm_video_path = self.storage_path / f"{recording_id}.webm"
                mp4_video_path = self.storage_path / f"{recording_id}.mp4"
                if not webm_video_path:
                    raise QCException.StepException(
                        f"Step: {last_step.get('id')} missing Recording. RecordID: {recording_id}")
                if not mp4_video_path.exists():
                    logger.warning(f"Step: {last_step.get('id')} recording not converted. RecordID: {recording_id}")
                    try:
                        convert_webm_to_mp4(webm_video_path, mp4_video_path)
                    except Exception as e:
                        raise QCException.StepException(
                            f"Step: {last_step.get('id')} Recording failed to convert. RecordID: {recording_id}")

                if os.path.exists(mp4_video_path):
                    # 获取视频最后一帧的时间戳
                    last_timestamp = get_video_duration_ms(mp4_video_path)
                    if last_timestamp is not None:
                        # 生成新的end步骤
                        new_step = {
                            "id": self.generate_random_id(len(last_step['id'])),
                            "title": "end",
                            "type": "click",
                            "devicePixelRatio": last_step.get('devicePixelRatio', 1),
                            "timestamp": int(last_timestamp),
                            "viewport": last_step.get('viewport', {'width': 1050, 'height': 759}),
                            "browserTopHeight": last_step.get('browserTopHeight', 0),
                            "createdTime": last_step.get('createdTime', 0)
                        }

                        # 添加新步骤
                        flow_content['steps'].append(new_step)
                        logger.warning(f"为任务添加了end步骤，ID: {new_step['id']}")
            else:
                logger.warning("Recording id not found in this instruction flow.")
        return flow_content

    def flow_process_merge_consecutive_scrolls(self, flow_content):
        """合并每个任务中连续的scroll操作，只保留最后一个并更新方向与距离"""
        if 'steps' not in flow_content or len(flow_content['steps']) == 0:
            raise QCException.FlowException(
                f"No steps in flow: {flow_content.get('id')}. Title: {flow_content.get('title')}")

        new_steps = []
        scroll_group = []

        for step in flow_content['steps']:
            if step.get('type') == 'scroll':
                scroll_group.append(step)
            else:
                # 处理已有的scroll group
                if scroll_group:
                    keep_step = self.merge_scroll_group_in_place(scroll_group)
                    new_steps.append(keep_step)
                    scroll_group = []
                new_steps.append(step)

        # 最后一组scroll
        if scroll_group:
            keep_step = self.merge_scroll_group_in_place(scroll_group)
            new_steps.append(keep_step)

        flow_content['steps'] = new_steps
        return flow_content

    def main(self):
        with open(self.json_path, 'r') as f:
            instruction_flows = json.load(f)
        for flow_content in tqdm.tqdm(instruction_flows):  # TODO: Refactor flow-wise process calling logic
            prev_flow_content = flow_content.copy()
            for idx, flow_process in enumerate(FLOW_PROCESSES):
                logger.info(f"[FLOW-PROCESS] {idx}. {flow_process}")
                try:
                    flow_content = self.__getattribute__(flow_process)(flow_content)
                    prev_flow_content = flow_content.copy()
                except Exception as e:
                    logger.error(traceback.print_exc())
                    logger.warning("Flow content will revert to previous step")
                    flow_content = prev_flow_content
            del prev_flow_content  # TODO: Check Memory clearing performance. Figure out more pythonic way to do this
            modified_steps = []
            for step_json in flow_content.get('steps'):  # TODO: Refactor step-wise process calling logic
                prev_step_json = step_json.copy()
                for idx, step_process in enumerate(STEP_PROCESSES):
                    logger.info(f"[STEP-PROCESS] {idx}. {step_process}")
                    try:
                        step_json = self.__getattribute__(step_process)(step_json)
                        prev_step_json = step_json.copy()
                    except Exception as e:
                        logger.error(traceback.print_exc())
                        logger.warning("Flow content will revert to previous step")
                        step_json = prev_step_json
                modified_steps.append(step_json)
                del prev_step_json
            flow_content['steps'] = modified_steps
        with open(self.json_path.parent / str(self.json_path.stem + '_updated.json'), 'w') as f:
            json.dump(instruction_flows, f, indent=4, ensure_ascii=False)
        logger.success(f"---- Flow {self.json_path} steps updated. ----")


if __name__ == "__main__":
    demo_json = "/Users/anthonyf/projects/grainedAI/WebAgentPipeline/src/sample_2_major_error/sample.json"
    legacy_image_path = "/src/sample_2_major_error/[好运来][temu]066"
    ins = JSONAutoQC(demo_json, legacy_image_path)
    ins.main()
