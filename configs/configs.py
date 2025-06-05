import yaml
from pathlib import Path

local_config_path = Path(__file__).parent/'configs.yaml'

with open(local_config_path, 'r') as f:
    configs = yaml.safe_load(f)

DEFAULT_VENDOR = "zhipu"
VLM_DEFAULT_MODEL_NAME = configs.get("VLM", {}).get(DEFAULT_VENDOR, {}).get("default_model_name")
LLM_DEFAULT_MODEL_NAME = configs.get("LLM", {}).get(DEFAULT_VENDOR, {}).get("default_model_name")

DEFAULT_VIEWPORT = {'width': 1050, 'height': 759}

STORAGE_PATH = configs.get('QCPipeline', {}).get('StoragePath')
VIDEO_STORAGE_PATH = configs.get('QCPipeline', {}).get('VideoStoragePath')
RAW_IMAGE_STORAGE_PATH = configs.get('QCPipeline', {}).get('RawImageStoragePath')
BBOXED_IMAGE_STORAGE_PATH = configs.get('QCPipeline', {}).get('BBoxedImageStoragePath')
ALL_JSON_STORAGE_PATH = configs.get('QCPipeline', {}).get('AllJSONPath')

DEFAULT_FLOW_CHECKS = configs.get('QCPipeline', {}).get('Main', {}).get('flow_checks', [])
DEFAULT_STEP_CHECKS = configs.get('QCPipeline', {}).get('Main', {}).get('step_checks', [])
# Fix
MAX_RETRY = 3
