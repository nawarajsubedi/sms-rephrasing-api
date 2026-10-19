from pydantic import BaseModel


class MessageRephrase(BaseModel):
    message: str
    member_id: str
    workspace_id: str


class RephraseResponse(BaseModel):
    data: list[str]
