import numpy as np
import cv2
import subprocess
from pathlib import Path
import json
from loguru import logger


# def convert_webm_to_mp4(webm_path, mp4_path):
#     """使用 ffmpeg 将 .webm 转换为 .mp4（加速随机访问）"""
#     cmd = [
#         'ffmpeg',
#         '-y',  # overwrite output
#         '-i', str(webm_path),
#         '-c:v', 'libx264',
#         '-preset', 'ultrafast',
#         '-pix_fmt', 'yuv420p',
#         str(mp4_path)
#     ]
#     logger.debug(f"-> {' '.join(cmd)}")
#     subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
#
#
# def extract_frame_at_timestamp(video_path, timestamp_ms, output_image_path):
#     """从视频中提取指定时间点的帧，单位为毫秒"""
#     cap = cv2.VideoCapture(str(video_path))
#     cap.set(cv2.CAP_PROP_POS_MSEC, timestamp_ms)
#     success, frame = cap.read()
#     if success:
#         if not output_image_path.exists():
#             os.makedirs(output_image_path.parent, exist_ok=True)
#         cv2.imwrite(str(output_image_path), frame)
#     cap.release()
#     return frame
#
def extract_frame_webm_at_timestamp(video_path, timestamp_ms, output_image_path):
    """从视频中提取指定时间点的帧，单位为毫秒"""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None

    logger.info(f"正在寻找时间戳: {timestamp_ms}ms")

    # 从头开始读取视频帧
    frame_buffer = None  # 保存上一帧
    last_time = 0  # 上一帧的时间戳

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        current_time = cap.get(cv2.CAP_PROP_POS_MSEC)

        # 打印调试信息
        logger.debug(f"当前帧时间戳: {current_time}ms")

        # 如果当前时间大于目标时间，返回较近的一帧
        if current_time >= timestamp_ms:
            # 判断哪一帧更接近目标时间戳
            if frame_buffer is not None and abs(last_time - timestamp_ms) < abs(current_time - timestamp_ms):
                logger.debug(f"使用缓存帧，时间戳: {last_time}ms")
                frame = frame_buffer
            else:
                logger.debug(f"使用当前帧，时间戳: {current_time}ms")
            break

        # 更新缓存
        frame_buffer = frame.copy()
        last_time = current_time

    cap.release()
    output_image_path = output_image_path.parent/str(output_image_path.stem+"_webm.jpeg")
    logger.debug(output_image_path)
    cv2.imwrite(str(output_image_path), frame)
    return frame
#
#
# def get_video_duration_ms(video_path):
#     """获取视频最后一帧的时间戳（单位：毫秒）"""
#     cmd = [
#         "ffprobe",
#         "-v", "error",
#         "-select_streams", "v:0",
#         "-show_entries", "format=duration",
#         "-of", "json",
#         str(video_path)
#     ]
#     result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
#     info = json.loads(result.stdout)
#     duration_seconds = float(info["format"]["duration"])
#     return int(duration_seconds * 1000)


# ----------------------------------------------------------------------
# 1) WebM → MP4：强制恒定帧率 (CFR) + 快速起播 + 关键帧间隔短
# ----------------------------------------------------------------------
def convert_webm_to_mp4(webm_path: Path | str,
                        mp4_path: Path | str,
                        fps: int = 30) -> None:
    """
    使用 FFmpeg 把 WebM 转为 MP4：
    - `fps`：输出恒定帧率；两端统一 seek 结果
    - `-movflags faststart`：写 moov box 在前，网页秒开
    - `-g 1 -bf 0`：全 I-帧（可选，进一步加速随机访问）
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", str(webm_path),
        "-vf", f"fps={fps}",
        "-c:v", "libx264", "-preset", "veryfast",
        "-pix_fmt", "yuv420p",
        "-movflags", "faststart",
        "-g", "1", "-bf", "0",
        str(mp4_path)
    ]
    logger.debug(" ".join(cmd))
    subprocess.run(cmd, stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=True)


# ----------------------------------------------------------------------
# 2) 按帧号精准取帧：兼容 MP4 / WebM
# ----------------------------------------------------------------------
def _seek_and_read(cap: cv2.VideoCapture,
                   frame_idx: int) -> tuple[bool, np.ndarray | None]:
    """
    先跳到目标前 1 帧以规避旧版 OpenCV“首帧空读” bug，
    再 grab 一次预热，最后 read 真实帧。
    """
    cap.set(cv2.CAP_PROP_POS_FRAMES, max(frame_idx - 1, 0))
    cap.grab()
    return cap.read()


def extract_frame_at_timestamp(video_path: Path | str,
                               timestamp_ms: int,
                               output_image_path: Path) -> np.ndarray | None:
    """
    按毫秒时间戳取帧（MP4 / WebM 通用）：
    1. 读取 FPS 与总帧数
    2. 计算目标帧号 N = round(t * fps)
    3. `_seek_and_read` 取帧；若失败 fallback 为逐帧扫描
    """
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        logger.error("无法打开视频：%s", video_path)
        return None

    fps   = cap.get(cv2.CAP_PROP_FPS)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if fps <= 0 or total <= 0:
        cap.release()
        logger.error("读取元数据失败：fps=%s, total=%s", fps, total)
        return None

    frame_idx = int(round(timestamp_ms / 1000 * fps))
    frame_idx = max(0, min(frame_idx, total - 1))

    success, frame = _seek_and_read(cap, frame_idx)

    # —— 兜底：如果首跳失败，逐帧拉到最近 —— #
    if not success or frame is None:
        logger.warning("按帧 seek 失败，回退逐帧扫描…")
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        buf, last_ts = None, 0
        while True:
            ret, fr = cap.read()
            if not ret:
                break
            cur_ts = cap.get(cv2.CAP_PROP_POS_MSEC)
            if cur_ts >= timestamp_ms:
                frame = fr if abs(cur_ts - timestamp_ms) < abs(last_ts - timestamp_ms) else buf
                break
            buf, last_ts = fr.copy(), cur_ts
        success = frame is not None

    cap.release()
    if not success:
        logger.error("解码失败：%s @ %d ms", video_path, timestamp_ms)
        return None

    output_image_path = Path(output_image_path)
    output_image_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_image_path), frame)
    return frame


def extract_frame_at_timestamp_pyav(video_path: Path | str,
                                    timestamp_ms: int,
                                    output_image_path: Path) -> np.ndarray | None:
    import av
    """
    修复的 PyAV 帧提取器 - 立即转换帧数据
    """
    try:
        with av.open(str(video_path)) as container:
            if not container.streams.video:
                logger.error("无视频流")
                return None

            video_stream = container.streams.video[0]
            target_sec = timestamp_ms / 1000.0

            logger.info(f"开始逐帧扫描，目标时间: {target_sec:.2f}s")

            # 重置到开头
            container.seek(0)

            best_frame_array = None
            best_diff = float('inf')
            frame_count = 0
            estimated_fps = 25.0  # 默认帧率

            for frame in container.decode(video_stream):
                frame_count += 1

                # 计算当前时间
                if frame.pts is not None and video_stream.time_base is not None:
                    try:
                        current_time_sec = float(frame.pts * video_stream.time_base)
                    except:
                        current_time_sec = frame_count / estimated_fps
                else:
                    current_time_sec = frame_count / estimated_fps

                diff = abs(current_time_sec - target_sec)

                # 如果找到更好的匹配，立即转换为 numpy 数组保存
                if diff < best_diff:
                    try:
                        # 立即转换帧数据，避免被后续循环覆盖
                        frame_array = frame.to_ndarray(format='bgr24')
                        best_frame_array = frame_array.copy()  # numpy 数组可以 copy
                        best_diff = diff
                        logger.debug(f"更好匹配: 帧{frame_count}, 时间={current_time_sec:.2f}s, 差异={diff:.3f}s")
                    except Exception as e:
                        logger.warning(f"帧转换失败: {e}")
                        continue

                # 进度报告
                if frame_count % 50 == 0:
                    logger.debug(f"扫描进度: {frame_count}帧, {current_time_sec:.1f}s")

                # 提前退出条件
                if current_time_sec > target_sec + 3.0:
                    logger.info(f"时间已超过目标，停止扫描")
                    break

                if diff < 0.05:  # 找到50ms内的精确匹配
                    logger.info(f"找到精确匹配，停止扫描")
                    break

                if frame_count > 999999999:  # 防止扫描过久
                    logger.warning(f"已扫描1000帧，强制停止")
                    break

            # 处理结果
            if best_frame_array is None:
                logger.error("未找到任何有效帧")
                return None

            # 保存文件
            try:
                output_image_path = Path(output_image_path)
                output_image_path.parent.mkdir(parents=True, exist_ok=True)

                success = cv2.imwrite(str(output_image_path), best_frame_array)
                if success:
                    logger.success(f"PyAV提取成功: 差异{best_diff:.3f}s, 文件: {output_image_path}")
                    return best_frame_array
                else:
                    logger.error("保存图片文件失败")
                    return None

            except Exception as e:
                logger.error(f"保存文件失败: {e}")
                return None

    except Exception as e:
        logger.error(f"PyAV异常: {e}")
        return None


# # 为向后兼容保留旧函数名
# extract_frame_webm_at_timestamp = extract_frame_at_timestamp


# ----------------------------------------------------------------------
# 3) 获取时长（毫秒）：先 ffprobe，失败再走 OpenCV
# ----------------------------------------------------------------------
def get_video_duration_ms(video_path: Path | str) -> int:
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "format=duration",
        "-of", "json", str(video_path)
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, check=True)
        seconds = float(json.loads(r.stdout)["format"]["duration"])
        return int(seconds * 1000)
    except Exception as e:
        logger.warning("ffprobe 失败 (%s)，改用 OpenCV 估算", e)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        logger.error("无法打开视频：%s", video_path)
        return 0
    fps   = cap.get(cv2.CAP_PROP_FPS)
    total = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    cap.release()
    return int(total / fps * 1000) if fps > 0 else 0

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
