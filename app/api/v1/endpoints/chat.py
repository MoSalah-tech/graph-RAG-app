import json
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from app.schemas.chat import ChatRequest, ChatResponse
from app.agents.finance_agent import build_agent

router = APIRouter()

# Cache agents per user_id so memory tools stay bound correctly
_agents: dict[str, object] = {}


def get_agent(user_id: str):
    if user_id not in _agents:
        _agents[user_id] = build_agent(user_id=user_id)
    return _agents[user_id]


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Non-streaming chat endpoint. Returns the full answer at once."""
    agent = get_agent(request.user_id)
    config = {"configurable": {"thread_id": request.session_id}}

    result = await agent.ainvoke(
        {"messages": [("user", request.message)]},
        config=config,
    )
    return ChatResponse(response=result["messages"][-1].content)


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint. Emits tokens as server-sent events."""
    agent = get_agent(request.user_id)
    config = {"configurable": {"thread_id": request.session_id}}

    async def event_generator():
        try:
            async for event in agent.astream_events(
                {"messages": [("user", request.message)]},
                config=config,
                version="v2",
            ):
                kind = event["event"]

                if kind == "on_chat_model_stream":
                    content = event["data"]["chunk"].content
                    if content:
                        yield {
                            "event": "token",
                            "data": json.dumps({"content": content}),
                        }
                elif kind == "on_tool_start":
                    yield {
                        "event": "tool",
                        "data": json.dumps({"tool": event["name"]}),
                    }
                elif kind == "on_tool_end":
                    yield {
                        "event": "tool_end",
                        "data": json.dumps({"tool": event["name"]}),
                    }

            yield {"event": "done", "data": "{}"}

        except Exception as e:
            yield {"event": "error", "data": json.dumps({"error": str(e)})}

    return EventSourceResponse(event_generator())