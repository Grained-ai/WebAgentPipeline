#!/usr/bin/env python3
"""
视频裁剪脚本
根据JSON文件中的recordingWindowRect信息裁剪视频，或复制原视频
"""

import json
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Set, Optional
from loguru import logger
import sys

def get_unique_recording_ids_and_rects(json_file: Path) -> Dict[str, Optional[Dict]]:
    """
    从JSON文件中提取所有唯一的recordingId和对应的recordingWindowRect
    
    Returns:
        Dict[str, Optional[Dict]]: {recordingId: recordingWindowRect or None}
    """
    logger.info(f"正在解析JSON文件: {json_file}")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    recording_data = {}
    
    # 遍历所有flow
    for flow in data:
        if 'steps' not in flow:
            continue
            
        # 遍历每个step
        for step in flow['steps']:
            recording_id = step.get('recordingId')
            if not recording_id:
                continue
                
            recording_window_rect = step.get('recordingWindowRect')
            
            # 如果这个recordingId还没有记录，或者当前step有recordingWindowRect而之前没有
            if (recording_id not in recording_data or 
                (recording_window_rect and not recording_data[recording_id])):
                recording_data[recording_id] = recording_window_rect
    
    logger.info(f"找到 {len(recording_data)} 个唯一的recordingId")
    
    # 统计有无recordingWindowRect的数量
    with_rect = sum(1 for rect in recording_data.values() if rect is not None)
    without_rect = len(recording_data) - with_rect
    
    logger.info(f"  - 有recordingWindowRect的: {with_rect}")
    logger.info(f"  - 无recordingWindowRect的: {without_rect}")
    
    return recording_data

def crop_video_with_ffmpeg(input_path: Path, output_path: Path, rect: Dict) -> bool:
    """
    使用ffmpeg裁剪视频
    
    Args:
        input_path: 输入视频路径
        output_path: 输出视频路径
        rect: recordingWindowRect字典，包含top, left, width, height
    
    Returns:
        bool: 是否成功
    """
    try:
        # 构建ffmpeg命令
        # crop=width:height:x:y
        crop_filter = f"crop={rect['width']}:{rect['height']}:{rect['left']}:{rect['top']}"
        
        cmd = [
            'ffmpeg',
            '-y',  # 覆盖输出文件
            '-i', str(input_path),
            '-vf', crop_filter,
            '-c:a', 'copy',  # 音频直接复制
            str(output_path)
        ]
        
        logger.debug(f"执行命令: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode == 0:
            logger.success(f"成功裁剪视频: {output_path}")
            return True
        else:
            logger.error(f"ffmpeg错误: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"裁剪视频时出错: {e}")
        return False

def copy_video(input_path: Path, output_path: Path) -> bool:
    """
    复制视频文件
    
    Args:
        input_path: 输入视频路径
        output_path: 输出视频路径
    
    Returns:
        bool: 是否成功
    """
    try:
        shutil.copy2(input_path, output_path)
        logger.success(f"成功复制视频: {output_path}")
        return True
    except Exception as e:
        logger.error(f"复制视频时出错: {e}")
        return False

def process_videos(json_file: Path, video_dir: Path, output_dir: Path = None) -> None:
    """
    处理所有视频
    
    Args:
        json_file: JSON文件路径
        video_dir: 视频文件目录
        output_dir: 输出目录，默认为视频文件目录
    """
    if output_dir is None:
        output_dir = video_dir
    
    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 获取recordingId和rect信息
    recording_data = get_unique_recording_ids_and_rects(json_file)
    
    success_count = 0
    error_count = 0
    missing_count = 0
    
    for recording_id, rect in recording_data.items():
        input_video = video_dir / f"{recording_id}.webm"
        output_video = output_dir / f"cropped_{recording_id}.webm"
        
        # 检查输入视频是否存在
        if not input_video.exists():
            logger.warning(f"视频文件不存在: {input_video}")
            missing_count += 1
            continue
        
        # 如果输出文件已存在，跳过
        if output_video.exists():
            logger.info(f"输出文件已存在，跳过: {output_video}")
            continue
        
        if rect:
            # 有recordingWindowRect，进行裁剪
            logger.info(f"裁剪视频 {recording_id} (rect: {rect})")
            if crop_video_with_ffmpeg(input_video, output_video, rect):
                success_count += 1
            else:
                error_count += 1
        else:
            # 没有recordingWindowRect，直接复制
            logger.info(f"复制视频 {recording_id}")
            if copy_video(input_video, output_video):
                success_count += 1
            else:
                error_count += 1
    
    # 输出统计信息
    logger.info("=" * 50)
    logger.info("处理完成统计:")
    logger.info(f"  - 成功处理: {success_count}")
    logger.info(f"  - 处理失败: {error_count}")
    logger.info(f"  - 视频文件缺失: {missing_count}")
    logger.info(f"  - 总计: {len(recording_data)}")

def main():
    """主函数"""
    # 配置路径
    json_file = Path("/Users/anthonyf/projects/grainedAI/WebAgentPipeline/scripts/adhoc/booking_2025-07-14.json")
    video_dir = Path("/Users/anthonyf/projects/grainedAI/WebAgentPipeline/scripts/data_files/for_XUEPENG")
    
    # 检查文件是否存在
    if not json_file.exists():
        logger.error(f"JSON文件不存在: {json_file}")
        sys.exit(1)
    
    if not video_dir.exists():
        logger.error(f"视频目录不存在: {video_dir}")
        logger.info("请确认视频文件的实际位置，并修改脚本中的video_dir路径")
        sys.exit(1)
    
    # 检查ffmpeg是否可用
    try:
        subprocess.run(['ffmpeg', '-version'], 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE, 
                      check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("ffmpeg未安装或不在PATH中，请先安装ffmpeg")
        sys.exit(1)
    
    logger.info("开始处理视频...")
    process_videos(json_file, video_dir)

if __name__ == "__main__":
    main()