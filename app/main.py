import logging

from fastapi import FastAPI, status
from fastapi.exceptions import HTTPException
from fastapi.responses import PlainTextResponse
from xlwings import XlwingsError

from . import api

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Don't expose the docs publicly
app = FastAPI(docs_url=None, redoc_url=None)

# Routers
app.include_router(api.router)


# Error handling: Unhandled errors will show "Internal Server Error"
@app.exception_handler(XlwingsError)
async def xlwings_exception_handler(request, exception):
    return PlainTextResponse(
        str(exception), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exception):
    # Return "msg" instead of {"detail": "msg"} for nicer frontend formatting
    return PlainTextResponse(str(exception.detail), status_code=exception.status_code)


# Unprotected health check
@app.get("/health")
async def health():
    return {"status": "ok"}
