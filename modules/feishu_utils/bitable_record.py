from loguru import logger
import json
from typing import Optional, Dict, Any, Self
# from modules.feishu_utils.bitable_ops import

from modules.webagent_data_utils import WebAgentStep


def _log_change(obj: Any, field: str, old_value: Any, new_value: Any):
    logger.info(
        f"{obj.__class__.__name__}[id={getattr(obj, 'id', 'unknown')}] updated '{field}' from '{old_value}' to '{new_value}'")

# def get_minimal_pattern(s: str) -> str:
#     """提取字符串（Double instruction_id）的最小重复单元"""
#     if not s:
#         return s
#
#     length = len(s)
#
#     # 从最小可能的模式开始检查
#     for i in range(1, length // 2 + 1):
#         if length % i == 0:  # 长度能被整除
#             pattern = s[:i]
#             if pattern * (length // i) == s:
#                 return pattern
#
#     # 如果没有重复模式，返回原字符串
#     return s


class BitableRecord:
    def __init__(self, record_dict: Dict[str, Any]):
        self._record_dict = record_dict
        self._record_fields = record_dict.get("fields")

    def __str__(self):
        return f"BitableRecord(record_id={self.record_id}, instruction_id='{self.instruction_id}'"

    @property
    def record_id(self) -> str:
        return self._record_dict.get("record_id")

    @property
    def instruction_id(self) -> str:
        instruction_id_column = self._record_fields.get("instruction_id")
        # return get_minimal_pattern(instruction_id_column[0].get("text")) if instruction_id_column else None
        return instruction_id_column[0].get("text")[:21] if instruction_id_column else None

    @property
    def instruction(self) -> str:
        instructions = self._record_fields.get("instructions")
        return "".join([instruction_item['text'] for instruction_item in instructions]) if instructions else None

    @property
    def title(self) -> str:
        return self.instruction

    @property
    def json_name(self) -> str:
        return self._record_fields.get("json_name")[0].get("text")

    @property
    def note(self) -> str:
        return self._record_fields.get("Note")[0].get("text")

    @property
    def parent_record_id(self) -> Self:
        link_record_ids = self._record_fields.get("Parent items").get("link_record_ids")
        return link_record_ids[0] if link_record_ids else None

    def get_value(self, key_name: str) -> str:
        return self._record_fields.get(key_name)

    def to_dict(self) -> Dict[str, Any]:
        return self._record_dict
