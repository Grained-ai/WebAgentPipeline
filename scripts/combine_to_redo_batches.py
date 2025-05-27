"""
batch_split.py
==============
• 读取一张任务总表 CSV
• 依据 “标注员 annotator” 分文件夹：
      <annotator>/
         ├─ owner_check.json            # website -> [完整 entry…]
         ├─ website_instructions.json   # website -> [title1, title2, …]
         └─ records.csv                 # 该 annotator 的全部原始行
"""

import csv, json
from pathlib import Path
from loguru import logger

# === 路径配置 =============================================================
JSON_ALL_PATH   = Path("/Users/anthonyf/projects/grainedAI/WebAgentPipeline/src/json_all")
INPUT_CSV       = Path("/Users/anthonyf/projects/grainedAI/WebAgentPipeline/src/redo_batches/20250526/QC_WebAgent_任务总表_打回要求表.csv")
SERVER_IMG_BASE = "http://3.145.59.104/checkingimg"        # 标注后图片外链前缀
# ==========================================================================


# ---------- JSON 工具函数 --------------------------------------------------
def index_all_json() -> dict[str, list]:
    """title -> [entry, entry…]"""
    title_map: dict[str, list] = {}
    for p in JSON_ALL_PATH.glob("*.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            logger.error(f"解析 {p.name} 失败: {e}")
            continue

        if not isinstance(data, list):
            continue

        for entry in data:
            title = (entry.get("title") or "").strip()
            if not title:
                continue
            entry["from_json"] = str(p.relative_to(JSON_ALL_PATH))
            title_map.setdefault(title, []).append(entry)
    logger.info(f"已索引 JSON title 共 {len(title_map)} 个")
    return title_map


def add_imgsave(entry: dict):
    stem = Path(entry["from_json"]).stem
    for step in entry.get("steps", []):
        if "img" in step:
            step["imgSave"] = f"{SERVER_IMG_BASE}/{stem}/{step['id']}_marked.jpeg"


def first_host(entry: dict) -> str:
    for s in entry.get("steps", []):
        h = (s or {}).get("host", "").strip()
        if h:
            return h
    return "unknown_site"


# ---------- 主流程 --------------------------------------------------------
def main(csv_path: Path):
    title_map = index_all_json()
    base_dir  = csv_path.parent                        # 与 CSV 同目录

    # Pass 0: 把 json_name -> annotator 的映射预取出来（用于补空 annotator）
    json2annot: dict[str, str] = {}
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            annot = (row.get("annotator") or "").strip()
            if annot:
                json2annot[row["json_name"]] = annot

    # Pass 1: 按 annotator 收集行 & 根指令（Parent items 为空）
    annot_rows   : dict[str, list[dict]] = {}      # annotator -> rows[]
    root_by_annot: dict[str, set[str]]   = {}      # annotator -> {root_title}

    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_annot = (row.get("annotator") or "").strip()
            annotator = raw_annot or json2annot.get(row["json_name"], "Unknown")
            annot_rows.setdefault(annotator, []).append(row)

            # 收根指令（instruction 非空且 Parent items 为空）
            inst        = (row.get("instruction") or "").strip()
            parent_item = (row.get("Parent items") or "").strip()
            if inst and not parent_item:
                root_by_annot.setdefault(annotator, set()).add(inst)

    logger.info(f"共发现 {len(annot_rows)} 位标注员")

    # Pass 2: 为每位 annotator 生成输出
    for ann, rows in annot_rows.items():
        logger.info(f"处理 {ann} …")
        # 2.1 owner_check  /  website_instructions
        by_site: dict[str, list] = {}
        for title in root_by_annot.get(ann, []):
            for entry in title_map.get(title, []):
                add_imgsave(entry)
                site = first_host(entry)
                by_site.setdefault(site, []).append(entry)

        site_titles = {s: sorted({e["title"] for e in lst}) for s, lst in by_site.items()}

        # 2.2 写文件
        out_dir = base_dir / ann
        out_dir.mkdir(exist_ok=True)

        (out_dir / "owner_check.json").write_text(
            json.dumps(by_site, ensure_ascii=False, indent=4), encoding="utf-8"
        )
        (out_dir / "website_instructions.json").write_text(
            json.dumps(site_titles, ensure_ascii=False, indent=4), encoding="utf-8"
        )

        # 2.3 直接把原始行写进 records.csv —— 完全保留顺序 / 列顺序
        rec_csv = out_dir / "records.csv"
        with rec_csv.open("w", newline="", encoding="utf-8-sig") as fw:
            writer = csv.DictWriter(fw, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

        logger.success(
            f"{ann}: owner_check={sum(len(v) for v in by_site.values())} 条, "
            f"records.csv 行数={len(rows)}"
        )


if __name__ == "__main__":
    main(INPUT_CSV)
