import traceback

import cv2
import json
import os
from PIL import Image, ImageDraw
import numpy as np
from datetime import datetime
import random
import string

def load_json_data(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_data(json_file, data):
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def generate_random_id(length):
    """生成指定长度的随机ID"""
    return ''.join(random.choices(string.ascii_letters + string.digits + '-_', k=length))

def get_last_frame_timestamp(video_path):
    """获取视频最后一帧的时间戳"""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None
    
    # 移动到视频末尾
    cap.set(cv2.CAP_PROP_POS_AVI_RATIO, 1)
    last_timestamp = cap.get(cv2.CAP_PROP_POS_MSEC)
    cap.release()
    return last_timestamp

def check_and_add_end_step(json_file, data,channelid):
    """检查每个任务的最后一步，如果不是end则添加end步骤"""
    modified = False
    # channelid = "1"
    for task in data:
        if 'steps' not in task or len(task['steps']) == 0:
            continue
            
        last_step = task['steps'][-1]
        print(last_step.get('title'))
        if last_step.get('title') != 'end':
            if last_step.get('title') != 'END':
                if last_step.get('title') != 'End':
                    # 获取recordingId和对应的视频文件路径
                    recording_id = None
                    for step in task['steps']:
                        if 'recordingId' in step:
                            recording_id = step['recordingId']
                            break
                    
                    if recording_id:
                        # 构建视频文件路径
                        base_name = os.path.splitext(os.path.basename(json_file))[0]
                        video_path = f"{base_name}_{channelid}/{recording_id}.webm"
                        # if os.path.exists(video_path):
                        if os.path.exists(video_path):
                            # 获取视频最后一帧的时间戳
                            last_timestamp = get_last_frame_timestamp(video_path)
                            if last_timestamp is not None:
                                print("111")
                                # 生成新的end步骤
                                new_step = {
                                    "id": generate_random_id(len(last_step['id'])),
                                    "title": "end",
                                    "type": "click",
                                    "devicePixelRatio": last_step.get('devicePixelRatio', 1),
                                    "timestamp": int(last_timestamp),
                                    "viewport": last_step.get('viewport', {'width': 1050, 'height': 759}),
                                    "browserTopHeight": last_step.get('browserTopHeight', 0),
                                    "createdTime": last_step.get('createdTime', 0)
                                }
                                
                                # 添加新步骤
                                task['steps'].append(new_step)
                                modified = True
                                print(f"为任务添加了end步骤，ID: {new_step['id']}")
    
    # 如果有修改，保存更新后的JSON文件
    if modified:
        save_json_data(json_file, data)
        print(f"JSON文件已更新: {json_file}")
    
    return data

def get_video_info(video_path):
    """获取视频信息"""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"无法打开视频文件: {video_path}")
    
    # 获取视频信息
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"\n原始视频尺寸: {width}x{height} 像素")
    
    # 手动计算总帧数和实际FPS
    total_frames = 0
    frame_times = []
    last_time = cap.get(cv2.CAP_PROP_POS_MSEC)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        current_time = cap.get(cv2.CAP_PROP_POS_MSEC)
        if current_time > 0:  # 确保时间戳有效
            frame_times.append(current_time - last_time)
            last_time = current_time
            
        total_frames += 1
    
    # 计算实际FPS
    if frame_times:
        # 移除异常值（比如第一帧可能不准确）
        frame_times = frame_times[1:]
        if frame_times:
            avg_frame_time = np.mean(frame_times)
            fps = 1000.0 / avg_frame_time  # 转换为每秒帧数
        else:
            fps = 30.0  # 默认值
    else:
        fps = 30.0  # 默认值
    
    # 重置视频到开始位置
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    cap.release()
    
    return {
        'fps': fps,
        'total_frames': total_frames,
        'width': width,
        'height': height
    }

def extract_frame_at_time(video_path, timestamp_ms, video_info):
    """从视频中提取指定时间戳的帧"""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None
    
    print(f"正在寻找时间戳: {timestamp_ms}ms")
    
    # 从头开始读取视频帧
    frame_buffer = None  # 保存上一帧
    last_time = 0  # 上一帧的时间戳
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        current_time = cap.get(cv2.CAP_PROP_POS_MSEC)
        
        # 打印调试信息
        print(f"当前帧时间戳: {current_time}ms")
        
        # 如果当前时间大于目标时间，返回较近的一帧
        if current_time >= timestamp_ms:
            # 判断哪一帧更接近目标时间戳
            if frame_buffer is not None and abs(last_time - timestamp_ms) < abs(current_time - timestamp_ms):
                print(f"使用缓存帧，时间戳: {last_time}ms")
                frame = frame_buffer
            else:
                print(f"使用当前帧，时间戳: {current_time}ms")
            break
            
        # 更新缓存
        frame_buffer = frame.copy()
        last_time = current_time
    
    cap.release()
    return frame

def mark_click_position(image, x, y, rect=None, radius=10):
    """在图片上标记点击位置和元素区域"""
    # 获取并打印图片尺寸
    height, width = image.shape[:2]
    print(f"截图尺寸: {width}x{height} 像素")
    
    # 转换OpenCV图片为PIL图片
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(image_rgb)
    draw = ImageDraw.Draw(pil_image)
    if x!=None and y!=None:
        # 绘制点击标记（十字线和圆圈）
        draw.ellipse([x-radius, y-radius, x+radius, y+radius], 
                    outline='red', width=2)
        draw.line([(x-radius, y), (x+radius, y)], fill='red', width=2)
        draw.line([(x, y-radius), (x, y+radius)], fill='red', width=2)
    
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

def merge_consecutive_scrolls(json_file, data):
    """合并每个任务中连续的scroll操作，只保留最后一个并更新方向与距离"""
    modified = False

    for task in data:
        if 'steps' not in task or len(task['steps']) == 0:
            continue
        
        new_steps = []
        scroll_group = []

        for step in task['steps']:
            if step.get('type') == 'scroll':
                scroll_group.append(step)
            else:
                # 处理已有的scroll group
                if scroll_group:
                    keep_step = merge_scroll_group_in_place(scroll_group)
                    new_steps.append(keep_step)
                    modified = True
                    scroll_group = []
                new_steps.append(step)

        # 最后一组scroll
        if scroll_group:
            keep_step = merge_scroll_group_in_place(scroll_group)
            new_steps.append(keep_step)
            modified = True

        task['steps'] = new_steps

    if modified:
        save_json_data(json_file, data)
        print(f"已合并scroll操作并更新JSON文件: {json_file}")

    return data


def merge_scroll_group_in_place(scroll_group):
    """合并scroll操作组，仅保留最后一个scroll，并修改其scrollDistance与scrollDirection"""
    if len(scroll_group) == 0:
        return None
    if len(scroll_group) == 1:
        return scroll_group[0]

    first = scroll_group[0]
    last = scroll_group[-1]

    # 计算合并后的 scrollDistance
    if first.get("scrollDirection")=="down": # 向下滚动起始点为 终点-向下距离
        first_diatance = first.get("scrollPosition", 0) - first.get("scrollDistance", 0)
        if first_diatance < 0:
            first_diatance = 0
    else: # 向上滚动起始点为 终点+向上距离
        if first.get("scrollPosition") == 0: # 在顶部向上滚动无效果
            first_diatance = 0
        else:
            first_diatance = first.get("scrollPosition", 0) + first.get("scrollDistance", 0)
    distance = abs(last.get("scrollPosition", 0) - first_diatance)
    # 统计总滚动距离按方向划分
    direction_totals = {"up": 0, "down": 0}
    for s in scroll_group:
        dir = s.get("scrollDirection", "down")
        dist = abs(s.get("scrollDistance", 0))
        if dir == "up" and s.get("scrollPosition")== 0:
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
    print(f"合并了 {len(scroll_group)} 个scroll操作 -> scrollDirection: {merged_direction}, scrollDistance: {distance}")
    return last


def process_recording(video_path, json_data, task_index, output_dir):
    """处理单个录制视频"""
    # 获取视频信息
    try:
        print(f"\n正在分析视频 {video_path}...")
        video_info = get_video_info(video_path)
        print(f"\n视频信息：")
        print(f"视频分辨率: {video_info['width']}x{video_info['height']} 像素")
        print(f"FPS: {video_info['fps']:.2f}")
        print(f"总帧数: {video_info['total_frames']}")
        print(f"视频时长: {video_info['total_frames']/video_info['fps']:.2f}秒")
        
        # 获取视频实际时长
        cap = cv2.VideoCapture(video_path)
        cap.set(cv2.CAP_PROP_POS_AVI_RATIO, 1)  # 移动到视频末尾
        actual_duration = cap.get(cv2.CAP_PROP_POS_MSEC)
        cap.release()
        print(f"实际视频时长: {actual_duration/1000:.2f}秒")
        
    except Exception as e:
        print(f"获取视频信息失败: {str(e)}")
        return
    
    # 获取当前任务数据
    task_data = json_data[task_index]
    
    # 获取所有时间戳（不预先减去100ms）
    timestamps = []
    for step in task_data['steps']:
        if 'timestamp' in step:  # 只要有timestamp的步骤都处理
            timestamps.append(step.get('timestamp', 0))
    
    # 按时间戳排序
    timestamps.sort()
    print(f"\n需要处理的时间戳: {timestamps}")
    
    # 获取viewport信息
    viewport = {'width': 1050, 'height': 759}  # 默认值
    
    # 用于合并连续的scroll操作
    merged_scrolls = []

    # 处理每个步骤
    for step in task_data['steps']:
        # 跳过没有timestamp的步骤（如launchApp等）
        if 'timestamp' not in step:
            continue
            
        # 获取时间戳
        timestamp = step['timestamp']
        created_time = step.get('createdTime', 0)
        action_title = step['title']
        print(f"\n处理步骤 {step['id']}:")
        print(f"操作类型: {step['type']}")
        print(f"时间戳: {timestamp}ms")
        
        # 处理负时间戳的情况
        is_negative_timestamp = timestamp < 0
        if is_negative_timestamp:
            # 使用负时间戳作为base值
            base = timestamp
            # 计算新的时间戳（createdTime + base - 50ms）
            actual_timestamp = created_time + base - 50
            print(f"检测到负时间戳，使用createdTime({created_time}) + base({base}) - 50ms = {actual_timestamp}ms")
            timestamp = actual_timestamp
        
        # 获取viewport信息（如果有）
        if 'viewport' in step:
            viewport = step['viewport']

        # 获取截图
        frame = extract_frame_at_time(video_path, timestamp, video_info)
        if frame is not None:
            # 获取设备像素比和浏览器顶部高度
            device_pixel_ratio = step.get('devicePixelRatio', 1)
            browser_top_height = int(step.get('browserTopHeight', 0))
            
            # 计算目标宽度和保持比例的高度
            target_width = int(viewport['width'] * device_pixel_ratio)
            # 获取原始图像的宽高
            orig_height, orig_width = frame.shape[:2]
            # 计算缩放比例
            scale_ratio = target_width / orig_width
            # 计算目标高度，保持原始宽高比
            target_height = int(orig_height * scale_ratio)
            
            print(f"原始尺寸: {orig_width}x{orig_height} 像素")
            print(f"目标尺寸: {target_width}x{target_height} 像素 (等比例缩放)")
            
            # 缩放图片
            frame_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            frame_resized = frame_pil.resize((target_width, target_height), Image.Resampling.LANCZOS)
            frame = cv2.cvtColor(np.array(frame_resized), cv2.COLOR_RGB2BGR)
            raw_output_path = f"{output_dir}_raw/{step['id']}_raw{'2' if is_negative_timestamp else ''}.jpeg"
            cv2.imwrite(raw_output_path, frame.copy())  # 使用 .copy() 防止后续修改影响原图
            print(f"保存原始截图: {raw_output_path}")
            # 如果是点击操作，标记点击位置
            if step['type'] == 'click' or step['type'] == 'type':
                # 获取点击坐标
                client_x = int(step.get('clientX', 0))
                client_y = int(step.get('clientY', 0))
                
                # 计算实际坐标
                x = int(client_x * device_pixel_ratio)
                y = int((client_y + browser_top_height) * device_pixel_ratio)
                
                # 获取rect信息并调整坐标
                rect = step.get('rect')
                if rect:
                    adjusted_rect = {
                        'left': int(rect['left'] * device_pixel_ratio),
                        'top': int((rect['top'] + browser_top_height) * device_pixel_ratio),
                        'right': int(rect['right'] * device_pixel_ratio),
                        'bottom': int((rect['bottom'] + browser_top_height) * device_pixel_ratio)
                    }
                else:
                    adjusted_rect = None
                
                print(f"原始坐标: clientX={client_x}, clientY={client_y}")
                print(f"浏览器顶部高度: {browser_top_height}")
                print(f"设备像素比: {device_pixel_ratio}")
                print(f"最终点击坐标: ({x}, {y})")
                if rect:
                    print(f"元素区域: left={adjusted_rect['left']}, top={adjusted_rect['top']}, right={adjusted_rect['right']}, bottom={adjusted_rect['bottom']}")
                if action_title != "end" and action_title != "End": 
                    # 标记点击位置和元素区域
                    frame = mark_click_position(frame, x, y, adjusted_rect)
            if step['type'] == 'scroll':
                if step['title'] == '局部向上滚动' or step['title'] == '局部向下滚动':
                    # 获取rect信息并调整坐标
                    rect = step.get('rect')
                    if rect:
                        adjusted_rect = {
                            'left': int(rect['left'] * device_pixel_ratio),
                            'top': int((rect['top'] + browser_top_height) * device_pixel_ratio),
                            'right': int(rect['right'] * device_pixel_ratio),
                            'bottom': int((rect['bottom'] + browser_top_height) * device_pixel_ratio)
                        }
                    else:
                        adjusted_rect = None
                    if action_title != "end" and action_title != "End": 
                        # 标记点击位置和元素区域
                        frame = mark_click_position(frame, None, None, adjusted_rect)

            # 保存截图
            output_path = f"{output_dir}/{step['id']}_marked{'2' if is_negative_timestamp else ''}.jpeg"
            cv2.imwrite(output_path, frame)
            print(f"保存截图: {output_path}")

def main(json_file,channelid):
    """主程序入口"""
    # 创建以JSON文件名为名的输出目录（不包含扩展名）
    base_name = os.path.splitext(os.path.basename(json_file))[0]
    output_dir = base_name
    output_dir_raw = base_name + "_raw"
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(output_dir_raw, exist_ok=True)
    # channelid = "1"
    # 加载JSON数据
    print(f"正在加载JSON文件: {json_file}")
    data = load_json_data(json_file)
    
    # 检查并添加end步骤
    data = check_and_add_end_step(json_file, data,channelid)
    data = merge_consecutive_scrolls(json_file, data)
    # 处理每个任务
    for i, task in enumerate(data):
        print(f"\n======= 处理任务 {i+1}/{len(data)} =======")
        
        # 获取recordingId
        if 'steps' not in task or len(task['steps']) == 0:
            print(f"任务 {i+1} 没有steps，跳过")
            continue
            
        # 查找有recordingId的step
        recording_id = None
        for step in task['steps']:
            if 'recordingId' in step:
                recording_id = step['recordingId']
                break
                
        if not recording_id:
            print(f"任务 {i+1} 没有找到recordingId，跳过")
            continue
            
        # 构建视频文件路径
        video_path = f"{base_name}_{channelid}/{recording_id}.webm"
        if not os.path.exists(video_path):
            print(f"视频文件不存在: {video_path}，跳过")
            continue
            
        print(f"找到视频文件: {video_path}")
        # 处理该任务的录像
        process_recording(video_path, data, i, output_dir)
        
    print(f"\n所有任务处理完成！截图已保存到 {output_dir} 目录")

if __name__ == "__main__":
    # import sys

    # if len(sys.argv) > 1:
    #     json_file = sys.argv[1]
    # else:
    #     json_file = "test.json"  # 默认JSON文件
    #
    # main(json_file)

    ## Anthony Added
    from pathlib import Path
    import glob
    from tqdm import tqdm
    from loguru import logger
    script_dir = Path(__file__).resolve().parent
    batch_dir = script_dir
    # todo_jobs = glob.glob(str(batch_dir/"*_*"))
    # todo_jobs = list(batch_dir.glob("*_*.json"))
    todo_jobs = [p for p in batch_dir.glob("*.json") if "_" not in p.stem]

    job_status = {}

    for job_json_path in tqdm(todo_jobs):
        jobname = job_json_path.stem
        logger.info(f"Working on job: {jobname}")
        video_folders = [p for p in batch_dir.glob(f"{jobname}_*") if p.is_dir() and not p.name.endswith("_raw")]
        if not video_folders:
            logger.warning(f"No video folder found for {jobname}")
            job_status[str(job_json_path)] = {
                'status': False,
                'log': "No matching video folder found"
            }
            continue

        # 处理所有匹配的视频文件夹（如需限定只能一个，也可加判断）
        for video_folder in video_folders:
            video_folder = video_folders[0]
            channel_id = video_folder.name.replace(f"{jobname}_", "")
            suffix = video_folder.name.replace(f"{jobname}_", "")
            job_raw_image_dir = batch_dir / f"{jobname}_raw"

            if job_raw_image_dir.exists():
                logger.success(f"{jobname} already finished.")
                job_status[str(job_json_path)] = {
                    'status': True,
                    'video_folder': video_folder.name,
                    'video_suffix': suffix
                }
                break  # 已完成，无需处理多个文件夹

            try:
                main(str(job_json_path),channel_id)
                job_status[str(job_json_path)] = {
                    'status': True,
                    'video_folder': video_folder.name,
                    'video_suffix': suffix
                }
            except Exception as e:
                logger.error(f"Failed to run {job_json_path.name}: {str(e)}")
                logger.warning(traceback.format_exc())
                job_status[str(job_json_path)] = {
                    'status': False,
                    'log': traceback.format_exc(),
                    'video_folder': video_folder.name,
                    'video_suffix': suffix
                }

            break

    # 保存任务状态
    with open(batch_dir / 'status.json', 'w') as f:
        json.dump(job_status, f, indent=4, ensure_ascii=False)
