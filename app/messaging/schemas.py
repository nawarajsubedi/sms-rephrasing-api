from pydantic import BaseModel, Field


class MessageRephrase(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    member_id: str
    workspace_id: str


class RephraseResponse(BaseModel):
    data: list[str]
