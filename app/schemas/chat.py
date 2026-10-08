from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str
    user_id: str = "default"
    session_id: str = "default"


class ChatResponse(BaseModel):
    response: str