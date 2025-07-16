import csv
import glob
import json
from pathlib import Path
from loguru import logger

BATCH_BASE = Path("/Users/anthonyf/projects/grainedAI/WebAgentPipeline/src/batches")
JSON_ALL_PATH = Path('/Users/anthonyf/projects/grainedAI/WebAgentPipeline/src/json_all')
INPUT_CSV = Path(
    '/Users/anthonyf/projects/grainedAI/WebAgentPipeline/src/batches/20250521/owner_check/QC_WebAgent_任务总表_Owner确认通过表 (4).csv')
SERVER_IMG_BASE = 'http://3.145.59.104/checkingimg'


def group_owner_check_instructions(csv_path: Path):
    raw_jsons = glob.glob(str(JSON_ALL_PATH / '*.json'))
    json_maps = {Path(i).stem: i for i in raw_jsons}
    # 输出目录
    out_dir = csv_path.parent
    out_dir.mkdir(exist_ok=True)
    # 1) 读 CSV，按 json 收集 instruction
    json_insts = {}
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            b = row["json_name"]
            batch_id = row['batch id']
            if 'w_check' in batch_id:
                b += "_w_check"
            inst = row["instruction"].strip()
            json_insts.setdefault(b, set()).add(inst)

    # 2) 全局加载所有 JSON 里的条目，按 title 建索引
    title_map = {}  # title -> list of entry dicts
    for path_str in raw_jsons:
        p = Path(path_str)
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[!] 无法解析 {p.name}: {e}")
            continue

        if isinstance(data, list):
            for item in data:
                title = item.get("title")
                if title:
                    item['from_json'] = str(p.relative_to(JSON_ALL_PATH))
                    title_map.setdefault(title.strip(), []).append(item)

    matched = []
    unknown_instructions = set()

    for json_flag in json_insts:
        inst_set = json_insts[json_flag]
        json_stem = json_flag.split('.json')[0]
        if json_stem not in json_maps:
            logger.error(f"{json_stem} not in json_map")
            unknown_instructions.update(inst_set)
            continue
        json_title_map = {}
        with open(json_maps[json_stem], 'r') as f:
            data = json.load(f)
        if isinstance(data, list):
            p = Path(json_maps[json_stem])
            for item in data:
                title = item.get("title")
                if title:
                    item['from_json'] = str(p.relative_to(JSON_ALL_PATH))
                    json_title_map.setdefault(title.strip(), []).append(item)
        for inst in inst_set:
            entries = json_title_map.get(inst)
            if entries:
                for entry in entries:
                    entry_from_json = Path(entry['from_json'])
                    for step in entry['steps']:
                        if 'img' in step:
                            step['imgSave'] = SERVER_IMG_BASE + "/" + str(entry_from_json.stem) + '/' + step['id'] + "_marked.jpeg"
                matched.extend(entries)
            else:
                logger.error(f"[!] 未在 {json_maps[json_stem]} 文件中找到标题：{inst}")

    for inst in unknown_instructions:
        entries = title_map.get(inst)
        if entries:
            for entry in entries:
                entry_from_json = Path(entry['from_json'])
                for step in entry['steps']:
                    if 'img' in step:
                        step['imgSave'] = SERVER_IMG_BASE + "/" + str(entry_from_json.stem) + '/' + step['id'] + "_marked.jpeg"
            matched.extend(entries)
            logger.success(f'Found {inst} in all batches')
        else:
            logger.error(f"[!] 未在任何 JSON 文件中找到标题：{inst}")

    # 4) 写出结果
    out_file = out_dir / f"owner_check.json"
    out_file.write_text(
        json.dumps(matched, ensure_ascii=False, indent=4),
        encoding="utf-8"
    )
    logger.success(f"✔️ Batch owner_check 共写入 {len(matched)} 条记录 到 {out_file}")


if __name__ == "__main__":
    group_owner_check_instructions(INPUT_CSV)
