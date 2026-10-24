import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.messaging.providers.base import ProviderError
from app.messaging.router import router as message_router
from app.messaging.router_v2 import router as message_router_v2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    get_settings()  # fail fast on invalid configuration
    yield


app = FastAPI(title="SMS Rephrasing API", lifespan=lifespan)


@app.exception_handler(ProviderError)
async def provider_error_handler(_: Request, exc: ProviderError) -> JSONResponse:
    logger.error("LLM provider request failed: %s (cause: %r)", exc, exc.__cause__)
    return JSONResponse(status_code=502, content={"detail": "AI provider unavailable"})


@app.get("/healthcheck", include_in_schema=False)
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(message_router, prefix="/message", tags=["Message (OpenAI)"])
app.include_router(message_router_v2, prefix="/v2/message", tags=["Message v2 (Bedrock)"])
