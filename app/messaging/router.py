from fastapi import APIRouter, Depends

from app.messaging.schemas import MessageRephrase, RephraseResponse
from app.messaging.service import RephraseService, get_rephrase_service

router = APIRouter()


@router.post("/rephrase", response_model=RephraseResponse)
async def rephrase(
    payload: MessageRephrase,
    service: RephraseService = Depends(get_rephrase_service),
) -> RephraseResponse:
    return RephraseResponse(data=await service.rephrase(payload.message))
