import os

import cv2
import subprocess
from pathlib import Path
import json
from loguru import logger


def convert_webm_to_mp4(webm_path, mp4_path):
    """使用 ffmpeg 将 .webm 转换为 .mp4（加速随机访问）"""
    cmd = [
        'ffmpeg',
        '-y',  # overwrite output
        '-i', str(webm_path),
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-pix_fmt', 'yuv420p',
        str(mp4_path)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def extract_frame_at_timestamp(video_path, timestamp_ms, output_image_path):
    """从视频中提取指定时间点的帧，单位为毫秒"""
    cap = cv2.VideoCapture(str(video_path))
    cap.set(cv2.CAP_PROP_POS_MSEC, timestamp_ms)
    success, frame = cap.read()
    if success:
        if not output_image_path.exists():
            os.makedirs(output_image_path.parent, exist_ok=True)
        cv2.imwrite(str(output_image_path), frame)
    cap.release()
    return frame


def get_video_duration_ms(video_path):
    """获取视频最后一帧的时间戳（单位：毫秒）"""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "format=duration",
        "-of", "json",
        str(video_path)
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    info = json.loads(result.stdout)
    duration_seconds = float(info["format"]["duration"])
    return int(duration_seconds * 1000)


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


# 示例用法
if __name__ == '__main__':
    webm_path = Path("/src/sample_1/mkacejtkxuvn1fzz7d5pug145ngew7.webm")
    mp4_path = Path("converted.mp4")
    output_frame_path = Path("frame_59549ms.jpg")  # 提取第 5.3 秒的帧

    # 转换格式以加速帧提取
    convert_webm_to_mp4(webm_path, mp4_path)

    # # 提取帧
    # success = extract_frame_at_timestamp(mp4_path, 59.549, output_frame_path)
    # if success:
    #     print(f"帧已保存至: {output_frame_path}")
    # else:
    #     print("帧提取失败")
    res = get_video_duration_ms(mp4_path)
    print(res)
