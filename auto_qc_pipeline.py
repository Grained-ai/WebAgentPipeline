import json
import shutil
import traceback
import yaml
from loguru import logger
from datetime import datetime, date
from pathlib import Path
from typing import Optional, Callable, Any, List
from tqdm import tqdm
import argparse

from modules.qc_exceptions import QCException
from modules.webagent_data_utils import WebAgentStep, WebAgentFlow
from configs.configs import DEFAULT_FLOW_CHECKS, DEFAULT_STEP_CHECKS, MAX_RETRY, STORAGE_PATH
import modules.instruction_level_check as flow_checks_mod
import modules.step_level_check as step_checks_mod
from modules.step_level_modification import label_bbox, visualize_delete_step


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
        problems: List[Any] = []
        success_count = 0
        failure_count = 0
        failure_details = []
        flows_data = json.loads(json_file.read_text(encoding="utf-8"))

        total_flows = len(flows_data)
        for flow_idx, flow_content in tqdm(list(enumerate(flows_data)), desc="Flow QC Progress"):
            flow = WebAgentFlow(flow_content)
            logger.info(f"========== 开始处理 Flow {flow_idx + 1}/{total_flows} (FlowID={flow.id}) ==========")

            for chk_name, chk_fn in zip(self.flow_check_names, self.flow_checks):
                retry = 0
                failure_idx = None
                while True:
                    # CHECK IF PROBLEM
                    prob = self._safe_run(chk_fn, flow)
                    if not prob:
                        success_count += 1
                        logger.success(f"[Flow#{flow.id}] ✔ {chk_name} 通过")
                        if failure_idx is not None:
                            failure_details[failure_idx]['resolved'] = True
                        break
                    problems.append(prob)
                    logger.warning(f"[Flow#{flow.id}] ⚠ {chk_name} 发现问题: {getattr(prob, 'detail', prob)}")
                    failure_count += 1
                    failure_idx = len(failure_details)
                    failure_details.append({
                        'flow_id': flow.id,
                        'step_id': None,
                        'chk_name': chk_name,
                        'error': getattr(prob, 'detail', prob),
                        'resolved': False
                    })
                    if not hasattr(prob, "fix") or retry >= MAX_RETRY:
                        logger.error(f"[Flow#{flow.id}] ❌ {chk_name} 无法自动修复 (retry={retry})")
                        break
                    # FIX PROBLEM
                    try:
                        prob.fix(flow)
                    except QCException as e:
                        logger.error(
                            f"[Flow#{flow.id}] ❌ {chk_name} 无法自动修复 (retry={retry}). [QC_Exception][{e}]")
                    except Exception as e:
                        logger.error(
                            f"[Flow#{flow.id}] ❌ {chk_name} 无法自动修复 (retry={retry}). [General_Exception][{e}]")

                    logger.info(f"[Flow#{flow.id}] 🔧 已尝试修复 {chk_name} (retry={retry})")
                    retry += 1

            total_steps = len(flow.steps)
            for step_idx, step_dict in tqdm(list(enumerate(flow.steps)), desc=f"Flow#{flow.id} Step QC Progress"):
                step = step_dict if isinstance(step_dict, WebAgentStep) else WebAgentStep(step_dict, parent_flow=flow)
                logger.info(
                    f"-- 正在处理 Step {step_idx + 1}/{total_steps} (StepID={step.id}) in Flow {flow_idx + 1}/{total_flows}")
                for chk_name, chk_fn in zip(self.step_check_names, self.step_checks):
                    retry = 0
                    failure_idx = None
                    while True:
                        prob = self._safe_run(chk_fn, step)
                        if not prob:
                            success_count += 1
                            logger.success(f"[Flow#{flow.id}/Step#{step.id}] ✔ {chk_name} 通过")
                            if failure_idx is not None:
                                failure_details[failure_idx]['resolved'] = True
                            break
                        problems.append(prob)
                        logger.warning(
                            f"[Flow#{flow.id}/Step#{step.id}] ⚠ {chk_name} 发现问题: "
                            f"{getattr(prob, 'detail', prob)}"
                        )
                        failure_count += 1
                        failure_idx = len(failure_details)
                        failure_details.append({
                            'flow_id': flow.id,
                            'step_id': step.id,
                            'chk_name': chk_name,
                            'error': getattr(prob, 'detail', prob),
                            'resolved': False
                        })
                        if not hasattr(prob, "fix"):
                            logger.error(
                                f"[Flow#{flow.id}/Step#{step.id}] ❌ {chk_name} 无法自动修复 (retry={retry}) [{prob} 没有对应的Fix method]"
                            )
                            break

                        if retry >= MAX_RETRY:
                            logger.error(
                                f"[Flow#{flow.id}/Step#{step.id}] ❌ {chk_name} 无法自动修复 (retry={retry}) [尝试次数超上线:{MAX_RETRY}]"
                            )
                            break
                        try:
                            prob.fix(step)
                        except QCException as e:
                            logger.error(
                                f"[Flow#{flow.id}/Step#{step.id}] ❌ {chk_name} 无法自动修复 (retry={retry}). [QC_Exception][{e}]")
                        except Exception as e:
                            logger.error(
                                f"[Flow#{flow.id}/Step#{step.id}] ❌ {chk_name} 无法自动修复 (retry={retry}). [General_Exception][{e}]")

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

        log_name = f"preprocessed_{json_file.stem}_{ts}_log.json"
        log_path = (self.storage_dir or json_file.parent) / log_name
        log_data = {
            'success_count': success_count,
            'failure_count': failure_count,
            'failure_details': failure_details
        }
        log_path.write_text(json.dumps(log_data, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.success(f"✅ 处理日志已保存到 {log_path}")

        return problems

    def preprocess_batch(self, json_files: List[Path]):
        for json_file in tqdm(json_files):
            self.preprocess(json_file)

    def postprocess_modification(self, json_file: Path):
        with open(json_file, 'r') as f:
            data = json.load(f)
        shutil.copy(json_file, json_file.parent / (json_file.stem + '_bak.json'))
        out = []
        for d in tqdm(data):
            flow_ins = WebAgentFlow(d)
            for step in flow_ins.steps:
                logger.info(f"BBoxing: {step.id}")
                try:
                    label_bbox(step, storage_path=STORAGE_PATH, ignore_missing_exception=True)
                except:
                    logger.error("Failed to label")
                    continue
                visualize_delete_step(step)
                native_drop_type_list = ['select', 'drag']
                if step.type in native_drop_type_list and any([i in step.title.lower() for i in native_drop_type_list]):
                    logger.debug(f"STEP.TYPE == {step.type}")
                    step.title = step.title + "[is_remake]"
                if '[not_is_remake]' in step.title and step.is_remake:
                    logger.debug("Revert is_remake flag")
                    step.is_remake = False
                    step.title = step.title.replace("[not_is_remake]", "")
                    step.title = step.title.replace('[is_remake]', '')

                if step.is_remake:
                    logger.debug("IS_REMAKE == TRUE")
                    step.title = step.title + "[is_remake]"
                if step.recrop_rect:
                    step.is_remake = False
                    step.title = step.title.replace("[is_remake]", "")
                    logger.debug(f'Current step title: {step.title}')
                logger.debug(step.qc_image_used)
            out.append(flow_ins.to_dict())
        with open(json_file, 'w') as f:
            json.dump(out, f, ensure_ascii=False, indent=4)
        return out

    def postprocess_modification_batch(self, json_files: List[Path]):
        for json_file in tqdm(json_files):
            logger.info(f"Applying: {json_file}")
            self.postprocess_modification(json_file)

    def deliver(self, json_file: Path):
        data = self.postprocess_modification(json_file)
        postprocess_count = len(data)
        out = []
        skipped_out = []
        for d in tqdm(data):
            flow_ins = WebAgentFlow(d)
            skip = False
            reason = None
            if '[REDO]' in flow_ins.title:
                logger.error(f"{flow_ins.title} is Discarded.")
                skip = True
                reason = 'REDO in title'
            for step in flow_ins.steps:
                logger.info(f"BBoxing: {step.id}")
                visualize_delete_step(step)
                if not step.deleted:
                    try:
                        label_bbox(step, storage_path=STORAGE_PATH, ignore_missing_exception=True)
                    except:
                        logger.error("Failed to label")
                        continue
                step._step_dict['recrop_rect'] = step.recrop_rect
                step.recrop_rect = None

                # if step.type in ['select', 'drag']:
                #     skip = True
            #     if not step.deleted and step.is_remake and '[REMOVED]' not in step.title and 'end' not in step.title.lower():
            #         reason = f'{step.title}:{step.deleted}, {step.is_remake}'
            #         skip = True
            #     logger.debug(step.qc_image_used)
            #
            # if not any([i.screenshot for i in flow_ins.steps]):
            #     logger.error(f"No screenshot flow {flow_ins.id}")
            #     skip = True
            #     reason = "NO screenshot"

            if skip:
                logger.error(f"{flow_ins.id} is discarded. {reason}")
                skipped_out.append(flow_ins.to_dict())
                continue

            out.append(flow_ins.to_dict())
        with open(json_file.parent / str("deliver_version_" + json_file.name), 'w') as f:
            json.dump(out, f, ensure_ascii=False, indent=4)
        with open(json_file.parent / str("skipped_" + json_file.name), 'w') as f:
            json.dump(skipped_out, f, ensure_ascii=False, indent=4)
        delivered_count = len(out)
        logger.success(f"post_processed count: {postprocess_count}")
        logger.success(f"Delivered count: {delivered_count}")

        return out

    def deliver_batch(self, json_files: List[Path]):
        total_outs = []
        for json_file in tqdm(json_files):
            logger.info(f"Re-bboxing: {json_file}")
            out = self.deliver(json_file)
            total_outs.append(out)

        apply_by_website = {}
        for data in total_outs:
            for i in data:
                f_i = WebAgentFlow(i)
                default_website_candi = [j for j in
                                         [i._step_dict.get("host") for i in f_i.steps]
                                         if j]
                default_website = default_website_candi[0] if default_website_candi else "UNKNOWN"
                if len(default_website.split('.')) > 2:
                    website = default_website.split('.')[1]
                elif len(default_website.split('.')) == 2:
                    website = default_website.split('.')[0]
                else:
                    website = "UNKNOWN"
                if website not in apply_by_website:
                    apply_by_website[website] = []
                if f_i.id in [i.get("id") for i in apply_by_website[website]]:
                    logger.warning(f"Skip redundant: {f_i.id}")
                else:
                    apply_by_website[website].append(f_i.to_dict())
        all_count = 0

        for key in apply_by_website:
            all_count += len(apply_by_website[key])
            with open(f"{key}_{date.today().strftime('%Y-%m-%d')}.json", 'w') as f:
                json.dump(apply_by_website[key], f, ensure_ascii=False, indent=4)
        logger.success(f"All: {sum([len(i) for i in total_outs])}")

    def extract_empty_frame_steps(self, json_files: List[Path]):
        pass


def main():
    parser = argparse.ArgumentParser(description="AutoQC Pipeline: Process JSON files to find issues.")
    parser.add_argument(
        'json_path',
        type=str,
        nargs='+',  # 允许传多个路径
        help="Path(s) to JSON file(s) to be processed"
    )
    parser.add_argument(
        '--redo_bbox',
        action='store_true',
        help="If set, will reprocess and relabel BBox for the JSON files"
    )
    parser.add_argument(
        '--deliver',
        action='store_true',
        help="If set, will reprocess and relabel BBox for the JSON files"
    )
    args = parser.parse_args()
    if len(args.json_path) == 1:
        logger.info(f"Working on {args.json_path[0]}")
        json_path = Path(args.json_path[0])
        pipeline = AutoQCPipeline()
        if args.deliver:
            logger.warning(f"Starts to deliver {args.json_path}")
            pipeline.deliver(json_path)
        elif args.redo_bbox:
            logger.warning(f"Starts to redo_bbox {args.json_path}")
            pipeline.postprocess_modification(json_path)

        else:
            logger.warning(f"Starts to pre_process {args.json_path}")
            issues = pipeline.preprocess(json_path)
            logger.success(f"✔ 共发现 {len(issues)} 个问题")
    else:
        logger.info(f"Working on batch: {args.json_path}")
        json_paths = [Path(p) for p in args.json_path]
        pipeline = AutoQCPipeline()
        if args.deliver:
            pipeline.deliver_batch(json_paths)
        elif args.redo_bbox:
            pipeline.postprocess_modification_batch(json_paths)
        else:
            pipeline.preprocess_batch(json_paths)
            logger.success(f"All finished.")


if __name__ == "__main__":
    main()
