from __future__ import annotations
from loguru import logger
from typing import Optional, Dict, Any
from configs.configs import DEFAULT_VIEWPORT
import json

from modules.qc_exceptions import FlowLoading, StepLoading


def _log_change(obj: Any, field: str, old_value: Any, new_value: Any):
    logger.info(
        f"{obj.__class__.__name__}[id={getattr(obj, 'id', 'unknown')}] updated '{field}' from '{old_value}' to '{new_value}'")


class WebAgentStep:
    def __init__(self, step_dict: Dict[str, Any], parent_flow: Optional[WebAgentFlow] = None):
        self._step_dict = step_dict
        self._flow = parent_flow

    @property
    def id(self) -> str:
        return self._step_dict.get("id")

    @property
    def type(self) -> str:
        return self._step_dict.get("type")

    @type.setter
    def type(self, value: str):
        old = self._step_dict.get("type")
        _log_change(self, "type", old, value)
        self._step_dict["type"] = value

    @property
    def title(self) -> Optional[str]:
        return self._step_dict.get("title")

    @title.setter
    def title(self, value: str):
        old = self._step_dict.get("title")
        _log_change(self, "title", old, value)
        self._step_dict["title"] = value

    @property
    def value(self) -> Optional[str]:
        return self._step_dict.get("value")

    @property
    def recording_id(self) -> Optional[str]:
        return self._step_dict.get("recordingId")

    @property
    def timestamp(self) -> Optional[int]:
        return self._step_dict.get("timestamp")

    @property
    def created_time(self) -> Optional[int]:
        return self._step_dict.get("createdTime", 0)

    @property
    def calibrated_timestamp_ms(self) -> int:
        return self.created_time + (self.timestamp or 0) if (self.timestamp and self.timestamp < 0) else (
                self.timestamp or 0)

    @property
    def viewport(self) -> Dict[str, Any]:
        return self._step_dict.get("viewport", DEFAULT_VIEWPORT)

    @property
    def device_pixel_ratio(self) -> float:
        return self._step_dict.get("devicePixelRatio", 1)

    @property
    def browser_top_height(self) -> int:
        return int(self._step_dict.get("browserTopHeight", 0))

    @property
    def rect(self) -> Optional[Dict[str, Any]]:
        return self._step_dict.get("rect")

    @property
    def adjusted_rect(self) -> Optional[Dict[str, int]]:
        if not self.rect:
            return None
        rect_info = {i: self.rect[i] for i in ['top', 'width', 'left', 'height']}
        rect_info['offset'] = self.browser_top_height
        top = int(rect_info['top'] * self.device_pixel_ratio)
        left = int(rect_info['left'] * self.device_pixel_ratio)
        width = int(rect_info['width'] * self.device_pixel_ratio)
        height = int(rect_info['height'] * self.device_pixel_ratio)
        offset = int(rect_info['offset'] * self.device_pixel_ratio)

        delta_h = 0 if self.rect["y"] != 0 else abs(self.rect["y"])
        delta_w = 0 if self.rect["x"] != 0 >= 0 else abs(self.rect["x"])

        # 计算右下角坐标
        bottom = top + height
        right = left + width
        return {
            'left': left + delta_w,
            'top': top + offset + delta_h,
            'right': right + delta_w,
            'bottom': bottom + offset + delta_h
        }
        # return {
        #     'left': int(self.rect['left'] * self.device_pixel_ratio),
        #     'top': int((self.rect['top'] + self.browser_top_height) * self.device_pixel_ratio),
        #     'right': int(self.rect['right'] * self.device_pixel_ratio),
        #     'bottom': int((self.rect['bottom'] + self.browser_top_height) * self.device_pixel_ratio)
        # }

    @property
    def screenshot(self) -> Optional[str]:
        return self._step_dict.get("screenshot")

    @screenshot.setter
    def screenshot(self, path: str):
        old = self._step_dict.get("screenshot")
        _log_change(self, "screenshot", old, path)
        self._step_dict["screenshot"] = path

    @property
    def marked_screenshot(self) -> Optional[str]:
        return self._step_dict.get("marked_screenshot")

    @marked_screenshot.setter
    def marked_screenshot(self, path: str):
        old = self._step_dict.get("marked_screenshot")
        _log_change(self, "marked_screenshot", old, path)
        self._step_dict["marked_screenshot"] = path

    @property
    def qc_image_used(self) -> Optional[str]:
        return self._step_dict.get("imgSave")

    @qc_image_used.setter
    def qc_image_used(self, path: str):
        old = self._step_dict.get("imgSave")
        _log_change(self, "imgSave", old, path)
        self._step_dict["imgSave"] = path

    @property
    def fix_methods(self) -> list[str]:
        return self._step_dict.setdefault("fix_methods", [])

    @property
    def deleted(self) -> bool:
        return self._step_dict.get("deleted", False)

    @property
    def deleted_by_qc(self) -> bool:
        return self._step_dict.get('isdeleted', False)

    @deleted.setter
    def deleted(self, value: bool):
        old = self._step_dict.get("deleted", False)
        _log_change(self, "deleted", old, value)
        self._step_dict["deleted"] = value

    @property
    def is_remake(self):
        return self._step_dict.get("isremake", False)

    @is_remake.setter
    def is_remake(self, value):
        old = self._step_dict.get("isremake", None)
        _log_change(self, "isremake", old, value)
        self._step_dict["isremake"] = value

    @property
    def recrop_rect(self):
        return self._step_dict.get('annotations', None)

    @recrop_rect.setter
    def recrop_rect(self, annotations):
        old = self._step_dict.get("annotations", False)
        _log_change(self, "annotations", old, annotations)
        self._step_dict["annotations"] = annotations

    @property
    def parent_flow(self) -> Optional[WebAgentFlow]:
        return self._flow

    def to_dict(self) -> Dict[str, Any]:
        return self._step_dict


class WebAgentFlow:
    def __init__(self, flow_dict: Dict[str, Any]):
        if 'steps' in flow_dict and isinstance(flow_dict['steps'], str):
            try:
                flow_dict['steps'] = json.loads(flow_dict['steps'])
                # logger.warning("Modified json steps from string to list")
            except json.JSONDecodeError as e:
                raise StepLoading(f"解析 steps 字段出错：{e}")
        self._flow_dict = flow_dict
        self._steps = [WebAgentStep(step, self) for step in flow_dict.get("steps", [])]

    @property
    def id(self) -> str:
        return self._flow_dict.get("id")

    @property
    def title(self) -> Optional[str]:
        return self._flow_dict.get("title").strip()

    @title.setter
    def title(self, value: str):
        old = self._flow_dict.get("title")
        _log_change(self, "title", old, value)
        self._flow_dict["title"] = value

    @property
    def steps(self) -> list[WebAgentStep]:
        return self._steps

    def to_dict(self) -> Dict[str, Any]:
        return self._flow_dict
