from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from app.agents.prompts import SYSTEM_PROMPT

from app.services.llm import get_llm
from app.agents.tools import ALL_TOOLS


def build_agent(user_id: str | None = None):
    llm = get_llm()
    from app.agents.tools import make_memory_tools

    tools = list(ALL_TOOLS)
    if user_id:
        tools.extend(make_memory_tools(user_id))

    return create_react_agent(
        llm,
        tools=tools,
        prompt=SYSTEM_PROMPT,
        checkpointer=MemorySaver(),
    )