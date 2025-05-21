from modules.utils import extract_frame_at_timestamp
from pathlib import Path
VIDEO_PATH = Path('/Users/anthonyf/projects/grainedAI/WebAgentPipeline/src/sample_1/mkacejtkxuvn1fzz7d5pug145ngew7.mp4')
TIMESTAMP = 97596
OUTPATH = Path('demo.jpeg')

extract_frame_at_timestamp(VIDEO_PATH,
                           TIMESTAMP,
                           OUTPATH)