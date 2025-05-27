from __future__ import annotations
from loguru import logger
from typing import Optional, Dict, Any
from configs.configs import DEFAULT_VIEWPORT


def _log_change(obj: Any, field: str, old_value: Any, new_value: Any):
    logger.info(f"{obj.__class__.__name__}[id={getattr(obj, 'id', 'unknown')}] updated '{field}' from '{old_value}' to '{new_value}'")


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
    def timestamp_ms(self) -> int:
        return self.created_time + (self.timestamp or 0) - 50 if (self.timestamp and self.timestamp < 0) else (self.timestamp or 0)

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
        return {
            'left': int(self.rect['left'] * self.device_pixel_ratio),
            'top': int((self.rect['top'] + self.browser_top_height) * self.device_pixel_ratio),
            'right': int(self.rect['right'] * self.device_pixel_ratio),
            'bottom': int((self.rect['bottom'] + self.browser_top_height) * self.device_pixel_ratio)
        }

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
        old = self._step_dict.get("qc_image_used")
        _log_change(self, "qc_image_used", old, path)
        self._step_dict["qc_image_used"] = path

    @property
    def fix_methods(self) -> list[str]:
        return self._step_dict.setdefault("fix_methods", [])

    @property
    def deleted(self) -> bool:
        return self._step_dict.get("deleted", False)

    @deleted.setter
    def deleted(self, value: bool):
        old = self._step_dict.get("deleted", False)
        _log_change(self, "deleted", old, value)
        self._step_dict["deleted"] = value

    @property
    def parent_flow(self) -> Optional[WebAgentFlow]:
        return self._flow

    def to_dict(self) -> Dict[str, Any]:
        return self._step_dict


class WebAgentFlow:
    def __init__(self, flow_dict: Dict[str, Any]):
        self._flow_dict = flow_dict
        self._steps = [WebAgentStep(step, self) for step in flow_dict.get("steps", [])]

    @property
    def id(self) -> str:
        return self._flow_dict.get("id")

    @property
    def title(self) -> Optional[str]:
        return self._flow_dict.get("title")

    @property
    def steps(self) -> list[WebAgentStep]:
        return self._steps

    def to_dict(self) -> Dict[str, Any]:
        return self._flow_dict
