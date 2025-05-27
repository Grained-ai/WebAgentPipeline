from modules.llm_utils.llm_factory import LLMFactory
from pathlib import Path
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser

class IfContainGotoLogic(BaseModel):
    if_contain_goto_logic: bool = Field(
        description="是否包含跳转到指定网站/网址的逻辑。"
    )
    reason: str = Field(
        description='判断原因'
    )

def check_if_goto_instruction(instruction):
    system_prompt_path = Path(__file__).parent / 'prompts' / 'check_contain_goto.prompt'
    with open(system_prompt_path, 'r') as f:
        prompt_template = f.read()
    parser = PydanticOutputParser(pydantic_object=IfContainGotoLogic)

    prompt = prompt_template.format(format_instructions=parser.get_format_instructions(),
                                    instruction=instruction)
    llm_ins = LLMFactory().create_llm_instance()
    res = llm_ins.invoke(prompt)
    answer = parser.parse(res.content)
    return answer.if_contain_goto_logic, answer.reason

