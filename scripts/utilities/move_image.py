import glob
import shutil
from pathlib import Path

import tqdm
import json


image_path_original = ""
image_path_add = ""

existing_imgs = [Path(i).name for i in glob.glob(str(Path(image_path_original)/'*.jpeg'))]

exist = []
copied = []
for image in tqdm.tqdm(Path(i) for i in glob.glob(str(Path(image_path_add)/'*.jpeg'))):
    if image.name in existing_imgs:
        exist.append(image)
    else:
        shutil.copy(image, image_path_original)
        copied.append(image)

with open("Copied.json", 'w') as f:
    json.dump(copied, f, indent=4, ensure_ascii=False)

with open("exists.json", 'w') as f:
    json.dump(exist, f, indent=4, ensure_ascii=False)

print(len(copied))
print(len(exist))

