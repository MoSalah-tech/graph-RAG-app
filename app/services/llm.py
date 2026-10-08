from langchain_openai import ChatOpenAI
from app.core.config import settings

def get_llm() -> ChatOpenAI:

    return ChatOpenAI(

        api_key=settings.OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
        model="nvidia/nemotron-3-super-120b-a12b:free",
        temperature=0,
        max_retries=3
        
    )