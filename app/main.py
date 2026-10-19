from fastapi import FastAPI

from app.messaging.router import router as message_router

app = FastAPI(title="SMS Rephrasing API")


@app.get("/healthcheck", include_in_schema=False)
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(message_router, prefix="/message", tags=["Message"])
