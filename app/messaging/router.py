from fastapi import APIRouter

from app.messaging import service
from app.messaging.schemas import MessageRephrase, RephraseResponse

router = APIRouter()


@router.post("/rephrase", response_model=RephraseResponse)
async def rephrase(payload: MessageRephrase) -> RephraseResponse:
    suggestions = await service.rephrase(payload.message)
    return RephraseResponse(data=suggestions)
