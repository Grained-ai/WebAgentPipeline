import json
from pathlib import Path

import tqdm
import re
from modules.webagent_data_utils import WebAgentFlow
import glob
from loguru import logger
all_good_preproess_empty_path = Path('/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/modification/20250603/subed_correct_version_w_chinese')
jsons = [i for i in glob.glob(str(all_good_preproess_empty_path/'*.json')) if 'log' not in i]
count = 0
for j in jsons:
    with open(j, 'r') as f:
        data = json.load(f)
    processed_data = []
    for i in data:
        f_i = WebAgentFlow(i)
        skipped = False
        for step in f_i.steps:
            if re.search(r"[\u4e00-\u9fff]", step.title or ""):
                skipped = True
        if skipped:
            continue
        processed_data.append(f_i.to_dict())
        count += 1
    with open(Path(j).stem.split('_')[1]+".json", 'w') as f:
        json.dump(processed_data, f, indent=4, ensure_ascii=False)

logger.info(f"Added: {count}")