import tqdm
from pathlib import Path
from modules.webagent_data_utils import WebAgentFlow
import glob
import json
from loguru import logger

all_good_preproess_empty_path = Path('/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/modification/20250609/prev_data_missed_v0')
jsons = [i for i in glob.glob(str(all_good_preproess_empty_path/'*.json')) if 'preprocessed' in i]

all_instructions = []

for j in tqdm.tqdm(jsons):
    with open(j, 'r') as f:
        data = json.load(f)
    for i in data:
        f_i = WebAgentFlow(i)
        skip = False
        for step in f_i.steps:
            if not step.screenshot:
                skip = True
                logger.info(j)
                break
        if not skip:
            all_instructions.append(i)

print(len(all_instructions))

chunk_size = 30
# 拆分成多个小文件
for i in range(0, len(all_instructions), chunk_size):
    chunk = all_instructions[i:i + chunk_size]
    chunk_index = i // chunk_size + 1
    output_path = f'check_fix_{chunk_index}.json'
    with open(output_path, 'w', encoding='utf-8') as out_f:
        json.dump(chunk, out_f, ensure_ascii=False, indent=2)
    print(f'Saved: {output_path}')