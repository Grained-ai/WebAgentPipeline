import time
from loguru import logger
from langchain_core.messages import HumanMessage, SystemMessage
from modules.llm_utils.llm_factory import LLMFactory
from modules.media_utils.image_ops import encode_image
from pathlib import Path
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser

class EnrichedStepResult(BaseModel):
    action: str = Field(
        description="English version action"
    )
    object: str = Field(
        description='English web element name。'
    )
    action_goal: str = Field(
        description='English version, the goal of the action. ie: action: click, object: close button, action_goal: close the tab.'
    )
    reason: str = Field(
        description='Reason for the enrichment. Include your assumed scenario. Concise in one sentence.'
    )

class SimpleTranslationResult(BaseModel):
    action: str = Field(
        description="English version action"
    )
    object: str = Field(
        description='English web element name'
    )
    reason: str = Field(
        description='Reason for the output. Concise in one sentence.'
    )

def translate_step_title(input_title, image_path):
    if not image_path:
        return simple_translate_step_title(input_title)
    try:
        if len(input_title.split(' ')) >= 4:
            logger.warning(f'Input title {input_title} length exceed threshold. Will do Enrich step title.')
            return enrich_step_title(input_title, image_path)
    except Exception as e:
        logger.error(str(e))
        pass
    return simple_translate_step_title(input_title)

def simple_translate_step_title(input_title):
    system_prompt_path = Path(__file__).parent / 'prompts' / 'simple_translate_step_title.prompt'
    with open(system_prompt_path, 'r') as f:
        prompt_template = f.read()
    parser = PydanticOutputParser(pydantic_object=SimpleTranslationResult)

    prompt = prompt_template.format(format_instructions=parser.get_format_instructions(),
                                    step_title=input_title,
                                    timestamps=str(time.time()*1000))
    llm_ins = LLMFactory().create_llm_instance()
    res = llm_ins.invoke(prompt)
    answer = parser.parse(res.content)
    return ' '.join([answer.action, answer.object])

def enrich_step_title(input_title, image_path):
    system_prompt_path = Path(__file__).parent / 'prompts' / 'enrich_step_title.prompt'
    with open(system_prompt_path, 'r') as f:
        prompt_template = f.read()
    parser = PydanticOutputParser(pydantic_object=EnrichedStepResult)

    prompt = prompt_template.format(format_instructions=parser.get_format_instructions())
    system_message = SystemMessage(content=prompt)
    text_message = {
        "type": "text",
        "text": f"这个图片上的操作现在叫做: {input_title}"
    }
    base64_image = encode_image(image_path)
    image_message = {
        "type": "image_url",
        "image_url": {'url': f"data:image/jpeg;base64,{base64_image}"}
    }
    # 创建人类消息，包含图像和文本
    human_message = HumanMessage(content=[text_message, image_message])
    llm_ins = LLMFactory().create_vllm_instance()
    res = llm_ins.invoke([system_message, human_message])
    answer = parser.parse(res.content)
    return ' '.join([answer.action, answer.object, f'to {answer.action_goal}'])