from loguru import logger
from langchain_openai import ChatOpenAI
try:
    from langchain_ollama import ChatOllama
except:
    logger.warning("Ollama is not supported.")
from configs.configs import *
class LLMFactory:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(LLMFactory, cls).__new__(cls)
            cls._instance.expense = {}
        return cls._instance

    @staticmethod
    def create_llm_instance(vendor=DEFAULT_VENDOR, model_name=LLM_DEFAULT_MODEL_NAME, temperature=0.95):
        with open(Path(__file__).parent.parent.parent / 'configs' / 'configs.yaml', 'r') as f:
            config = yaml.safe_load(f)

        if model_name is None:
            model_name = LLM_DEFAULT_MODEL_NAME

        if model_name.startswith("OLLAMA"):
            return ChatOllama(
                temperature=temperature,
                model=config['LLM'][model_name]['llm_params']['model_name']
            )
        else:
            return ChatOpenAI(
                temperature=temperature,
                model=model_name,
                openai_api_key=config['VLM'][vendor]['api_key'],
                openai_api_base=config['VLM'][vendor]['endpoint']
            )

    @staticmethod
    def create_vllm_instance(vendor=DEFAULT_VENDOR, model_name=VLM_DEFAULT_MODEL_NAME, temperature=0.95):
        with open(Path(__file__).parent.parent.parent / 'configs' / 'configs.yaml', 'r') as f:
            config = yaml.safe_load(f)

        return ChatOpenAI(
            model=model_name,
            openai_api_key=config['VLM'][vendor]['api_key'],
            openai_api_base=config['VLM'][vendor]['endpoint'],
            temperature=temperature
        )

if __name__ == "__main__":
    ins = LLMFactory()
    a = ins.create_llm_instance()
    print(a.invoke("HI"))