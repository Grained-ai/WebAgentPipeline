from loguru import logger
from PIL import Image, ImageDraw
import numpy as np
import cv2
import base64

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
                               outline='green',
                               width=2,
                               fill=(255, 0, 0, 30))  # 半透明红色填充
        # 将半透明层合并到原图
        pil_image = Image.alpha_composite(pil_image.convert('RGBA'), overlay)

    # 转换回OpenCV格式
    return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGBA2BGR)

def encode_image(image_path):
    """将图像转换为 Base64 编码"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def mark_redo_bbox(image, annotations):
    """
    根据 ratio 信息将标注矩形画到图像上。
    """
    draw = ImageDraw.Draw(image)
    img_w, img_h = image.size

    for ann in annotations:
        if ann.get("type") == "rect":
            # 从比例还原为实际像素
            x1 = ann["xRatio"] * img_w
            y1 = ann["yRatio"] * img_h
            x2 = x1 + (ann["widthRatio"] * img_w)
            y2 = y1 + (ann["heightRatio"] * img_h)

            draw.rectangle([x1, y1, x2, y2], outline="red", width=3)
    return image
