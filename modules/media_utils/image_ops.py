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

def crop_browser_from_desktop(desktop_image, recording_window_rect, browser_top_height, viewport, output_path=None):
    """
    从桌面整体截图中提取浏览器内容

    Args:
        desktop_image: 桌面整体截图 (numpy array 或 PIL Image)
        recording_window_rect: 浏览器窗口位置信息
                             {'left': int, 'top': int, 'width': int, 'height': int}
        browser_top_height: 浏览器导航栏+书签栏的高度
        viewport: 浏览器视窗信息 {'width': int, 'height': int}
        output_path: 可选，保存路径

    Returns:
        dict: 包含不同部分的截图
        {
            'full_browser': 完整浏览器窗口截图,
            'navigation_bar': 导航栏+书签栏截图,
            'viewport_area': 视窗区域截图
        }
    """
    # 转换输入图像为numpy array
    if isinstance(desktop_image, Image.Image):
        desktop_array = np.array(desktop_image)
    else:
        desktop_array = desktop_image.copy()

    # 获取桌面截图尺寸
    desktop_height, desktop_width = desktop_array.shape[:2]
    logger.info(f"桌面截图尺寸: {desktop_width}x{desktop_height} 像素")

    # 提取浏览器窗口位置信息
    browser_left = recording_window_rect['left']
    browser_top = recording_window_rect['top']
    browser_width = min(recording_window_rect['width'], viewport['width'])
    browser_height = min(recording_window_rect['height'], viewport['height'])

    logger.info(f"浏览器窗口位置: ({browser_left}, {browser_top})")
    logger.info(f"浏览器窗口尺寸: {browser_width}x{browser_height}")
    logger.info(f"导航栏高度: {browser_top_height}")
    logger.info(f"视窗尺寸: {viewport['width']}x{viewport['height']}")

    # 边界检查
    if (browser_left + browser_width > desktop_width or
            browser_top + browser_height > desktop_height or
            browser_left < 0 or browser_top < 0):
        logger.warning("浏览器窗口超出桌面边界，将调整截取范围")
        browser_left = max(0, browser_left)
        browser_top = max(0, browser_top)
        browser_width = min(browser_width, desktop_width - browser_left)
        browser_height = min(browser_height, desktop_height - browser_top)

    # 截取完整浏览器窗口
    full_browser = desktop_array[
                   browser_top:browser_top + browser_height,
                   browser_left:browser_left + browser_width
                   ]

    # 截取导航栏+书签栏区域
    nav_bar_height = min(browser_top_height, browser_height)
    navigation_bar = desktop_array[
                     browser_top:browser_top + nav_bar_height,
                     browser_left:browser_left + min(viewport['width'], browser_width)
                     ]

    # 截取视窗区域（去除导航栏）
    viewport_start_y = browser_top + browser_top_height
    viewport_height = min(viewport['height'], browser_height - browser_top_height)
    viewport_width = min(viewport['width'], browser_width)
    # viewport_width = browser_width

    if viewport_height > 0 and viewport_width > 0:
        viewport_area = desktop_array[
                        viewport_start_y:viewport_start_y + viewport_height,
                        browser_left:browser_left + viewport_width
                        ]
    else:
        logger.warning("视窗区域计算异常，创建空白图像")
        viewport_area = np.zeros((100, 100, 3), dtype=np.uint8)

    result = {
        'full_browser': full_browser,
        'navigation_bar': navigation_bar,
        'viewport_area': viewport_area
    }

    # 保存图像（如果指定了输出路径）
    if output_path:
        from pathlib import Path
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        # 保存各个部分
        cv2.imwrite(str(output_path / "full_browser.png"), full_browser)
        cv2.imwrite(str(output_path / "navigation_bar.png"), navigation_bar)
        cv2.imwrite(str(output_path / "viewport_area.png"), viewport_area)

        logger.success(f"浏览器截图已保存到: {output_path}")

    # 打印截取结果信息
    logger.info("截取结果:")
    logger.info(f"  完整浏览器: {full_browser.shape[1]}x{full_browser.shape[0]}")
    logger.info(f"  导航栏区域: {navigation_bar.shape[1]}x{navigation_bar.shape[0]}")
    logger.info(f"  视窗区域: {viewport_area.shape[1]}x{viewport_area.shape[0]}")

    return result

