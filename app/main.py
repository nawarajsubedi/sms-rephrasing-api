import logging

import openai
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.messaging.router import router as message_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SMS Rephrasing API")


@app.exception_handler(openai.OpenAIError)
async def openai_error_handler(_: Request, exc: openai.OpenAIError) -> JSONResponse:
    logger.error("OpenAI request failed: %s", exc)
    return JSONResponse(status_code=502, content={"detail": "AI provider unavailable"})


@app.get("/healthcheck", include_in_schema=False)
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(message_router, prefix="/message", tags=["Message"])
