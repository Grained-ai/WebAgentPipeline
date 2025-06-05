"""
qc_problems.py
==============
• 不再使用 Enum；问题类型直接用字符串常量
• @register_problem("<TYPE_NAME>") 把类注册进全局 PROBLEM_REGISTRY
• ProblemBase.type → str
"""

from dataclasses import dataclass, field
from typing import Callable, Union, Type, Dict, List
from modules.webagent_data_utils import WebAgentStep, WebAgentFlow

# --------------------------------------------------
# 注册表：问题类型字符串 → 问题类
# --------------------------------------------------
PROBLEM_REGISTRY: Dict[str, Type["ProblemBase"]] = {}


def register_problem(type_name: str):
    """
    装饰器：显式指定问题类型字符串。
    用法:
        @register_problem("MISSING_END_STEP")
        class MissingEndProblem(ProblemBase):
            ...
    """

    def decorator(cls: Type["ProblemBase"]):
        if type_name in PROBLEM_REGISTRY:
            raise ValueError(f"重复注册问题类型 {type_name}")
        cls.type = type_name  # ← 直接是 str
        PROBLEM_REGISTRY[type_name] = cls
        return cls

    return decorator


# --------------------------------------------------
# Problem 基类
# --------------------------------------------------
@dataclass
class ProblemBase:
    detail: str = ""
    kwargs: dict = field(default_factory=dict)

    @property
    def type(self) -> property:  # 现在就是 str
        return self.__class__.type

    @property
    def pipeline(self) -> List[Callable]:
        raise NotImplementedError

    def fix(self, content: Union[WebAgentStep, WebAgentFlow]):
        """
        顺序调用 pipeline 中的修改函数；
        每个函数应当返回修改后的 content
        """
        for func in self.pipeline:
            content = func(content, **self.kwargs)
        return content


# --------------------------------------------------
# 具体问题类 —— 下面示例保留了与你原文件一致的名称/逻辑
# --------------------------------------------------
from modules.step_level_modification import (
    step_title_chinese2english,
    delete_step,
    mark_new_bbox,
    mark_modify_title,
    extract_blank_frame,
    label_bbox,
    substitute_step_type,
    assign_qc_image_used,
    visualize_delete_step
)
from modules.instruction_level_modification import (
    merge_consecutive_scrolls,
    check_and_add_end_step,
    delete_first_launch_app,
    instruction_level_modify_step_type
)


@register_problem("CHINESE_IN_TITLE")
class ChineseInTitleProblem(ProblemBase):
    pipeline = [step_title_chinese2english]


@register_problem("MISSING_END_STEP")
class MissingEndProblem(ProblemBase):
    pipeline = [check_and_add_end_step]


@register_problem("CONSECUTIVE_SCROLLS")
class ConsecutiveScrollsProblem(ProblemBase):
    pipeline = [merge_consecutive_scrolls]


@register_problem("REDUNDANT_LAUNCHAPP")  # 同一类型可对应多个修复策略
class RedundantLaunchAppProblem(ProblemBase):
    pipeline = [delete_first_launch_app]


@register_problem("MISSING_BBOX")
class MissingBBoxProblem(ProblemBase):
    pipeline = [mark_new_bbox]


@register_problem("VAGUE_TITLE")
class VagueStepTitleProblem(ProblemBase):
    pipeline = [mark_modify_title]


@register_problem("MISSING_FRAME")
class MissingBlankScreenshotProblem(ProblemBase):
    pipeline = [extract_blank_frame]


@register_problem("BBOX_NOT_MARKED")
class MissingMarkedScreenshotProblem(ProblemBase):
    pipeline = [label_bbox]


@register_problem("WRONG_STEP_TYPE")
class WrongStepTypeProblem(ProblemBase):
    pipeline = [substitute_step_type]


@register_problem("MISSING_QC_IMAGE_PATH")
class MissingQCImagePath(ProblemBase):
    pipeline = [assign_qc_image_used]


@register_problem("INSTRUCTION_LEVEL_WRONG_STEP_TYPE")
class InstructionLevelWrongStepTypes(ProblemBase):
    pipeline = [instruction_level_modify_step_type]


@register_problem("NEED_TO_VISUALIZE_DELETED_STEP")
class NeedVisualizeDelete(ProblemBase):
    pipeline = [visualize_delete_step]


# --------------------------------------------------
# 工具函数：查看当前已注册的问题 ↔ 类型
# --------------------------------------------------
def list_all_problem_types():
    return [(cls.__name__, cls.type) for cls in PROBLEM_REGISTRY.values()]
