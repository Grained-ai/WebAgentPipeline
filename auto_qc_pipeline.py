import json
import traceback
import yaml
from loguru import logger
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, Any, List
from tqdm import tqdm

from modules.qc_exceptions import QCException
from modules.webagent_data_utils import WebAgentStep, WebAgentFlow
from configs.configs import DEFAULT_FLOW_CHECKS, DEFAULT_STEP_CHECKS
import modules.instruction_level_check as flow_checks_mod
import modules.step_level_check as step_checks_mod


class AutoQCPipeline:
    def __init__(self, config_path: Optional[Path] = None):
        if config_path:
            cfg = yaml.safe_load(Path(config_path).read_text()) or {}
            qc_main = cfg.get("QCPipeline", {}).get("Main", {})
            flow_check_names = qc_main.get("flow_checks", []) or DEFAULT_FLOW_CHECKS
            step_check_names = qc_main.get("step_checks", []) or DEFAULT_STEP_CHECKS
            self.storage_dir = Path(cfg.get("QCPipeline", {}).get("StoragePath", "./storage"))
        else:
            flow_check_names = DEFAULT_FLOW_CHECKS
            step_check_names = DEFAULT_STEP_CHECKS
            self.storage_dir = None

        self.flow_check_names = list(dict.fromkeys(flow_check_names))
        self.step_check_names = list(dict.fromkeys(step_check_names))

        self.flow_checks = [self._resolve_callable(n, is_flow=True) for n in self.flow_check_names]
        self.step_checks = [self._resolve_callable(n, is_flow=False) for n in self.step_check_names]

        if self.storage_dir:
            self.storage_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _resolve_callable(name: str, *, is_flow: bool) -> Callable:
        module = flow_checks_mod if is_flow else step_checks_mod
        if hasattr(module, name):
            return getattr(module, name)
        raise ImportError(f"❌ 在 {module.__name__} 中找不到检查函数 '{name}'")

    @staticmethod
    def _safe_run(fn: Callable, target) -> Any:
        try:
            return fn(target)
        except Exception as e:
            logger.error(f"[QC ERROR] {fn.__name__}: {e}")
            logger.warning(traceback.print_exc())
            return None

    def preprocess(self, json_file: Path) -> List[Any]:
        MAX_RETRY = 3
        problems: List[Any] = []
        flows_data = json.loads(json_file.read_text(encoding="utf-8"))

        for flow_idx, flow_content in tqdm(list(enumerate(flows_data)), desc="Flow QC Progress"):
            flow = WebAgentFlow(flow_content)

            for chk_name, chk_fn in zip(self.flow_check_names, self.flow_checks):
                retry = 0
                while True:
                    prob = self._safe_run(chk_fn, flow)
                    if not prob:
                        logger.success(f"[Flow#{flow.id}] ✔ {chk_name} 通过")
                        break
                    problems.append(prob)
                    logger.warning(f"[Flow#{flow.id}] ⚠ {chk_name} 发现问题: {getattr(prob, 'detail', prob)}")
                    if not hasattr(prob, "fix") or retry >= MAX_RETRY:
                        logger.error(f"[Flow#{flow.id}] ❌ {chk_name} 无法自动修复 (retry={retry})")
                        break
                    prob.fix(flow)
                    logger.info(f"[Flow#{flow.id}] 🔧 已尝试修复 {chk_name} (retry={retry})")
                    retry += 1

            for step_idx, step_dict in tqdm(list(enumerate(flow.steps)), desc=f"Flow#{flow.id} Step QC Progress"):
                step = step_dict if isinstance(step_dict, WebAgentStep) else WebAgentStep(step_dict, parent_flow=flow)
                for chk_name, chk_fn in zip(self.step_check_names, self.step_checks):
                    retry = 0
                    while True:
                        prob = self._safe_run(chk_fn, step)
                        if not prob:
                            logger.success(f"[Flow#{flow.id}/Step#{step.id}] ✔ {chk_name} 通过")
                            break
                        problems.append(prob)
                        logger.warning(
                            f"[Flow#{flow.id}/Step#{step.id}] ⚠ {chk_name} 发现问题: "
                            f"{getattr(prob, 'detail', prob)}"
                        )
                        if not hasattr(prob, "fix") or retry >= MAX_RETRY:
                            logger.error(
                                f"[Flow#{flow.id}/Step#{step.id}] ❌ {chk_name} 无法自动修复 (retry={retry}) [{prob} 没有对应的Fix method]"
                            )
                            break
                        try:
                            prob.fix(step)
                        except QCException as e:
                            logger.error(f"[Flow#{flow.id}/Step#{step.id}] ❌ {chk_name} 无法自动修复 (retry={retry}). [QC_Exception][{e}]")
                        except Exception as e:
                            logger.error(f"[Flow#{flow.id}/Step#{step.id}] ❌ {chk_name} 无法自动修复 (retry={retry}). [General_Exception][{e}]")

                        logger.info(f"[Flow#{flow.id}/Step#{step.id}] 🔧 已尝试修复 {chk_name} (retry={retry})")
                        retry += 1

            if hasattr(flow, "to_dict") and callable(flow.to_dict):
                flows_data[flow_idx] = flow.to_dict()
            else:
                flows_data[flow_idx] = flow_content

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_name = f"preprocessed_{json_file.stem}_{ts}.json"
        out_path = (self.storage_dir or json_file.parent) / out_name
        out_path.write_text(json.dumps(flows_data, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.success(f"✅ 预处理完成，已保存到 {out_path}")

        return problems


if __name__ == "__main__":
    pipeline = AutoQCPipeline()
    issues = pipeline.preprocess(Path("/Users/anthonyf/projects/grainedAI/WebAgentPipeline/src/batches/20250522/delivery/zhipu_220_20250522_171937.json"))
    print(f"✔ 共发现 {len(issues)} 个问题")
