import yaml
from pathlib import Path

local_config_path = Path(__file__).parent/'configs.yaml'

with open(local_config_path, 'r') as f:
    configs = yaml.safe_load(f)

DEFAULT_VENDOR = "zhipu"
VLM_DEFAULT_MODEL_NAME = configs.get("VLM", {}).get(DEFAULT_VENDOR, {}).get("default_model_name")
LLM_DEFAULT_MODEL_NAME = configs.get("LLM", {}).get(DEFAULT_VENDOR, {}).get("default_model_name")