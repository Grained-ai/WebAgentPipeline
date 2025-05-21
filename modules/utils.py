import os

import cv2
import subprocess
from pathlib import Path
import json

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

# 示例用法
if __name__ == '__main__':
    webm_path = Path("/Users/anthonyf/projects/grainedAI/WebAgentPipeline/src/sample_1/mkacejtkxuvn1fzz7d5pug145ngew7.webm")
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