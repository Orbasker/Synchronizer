import os
from datetime import datetime, timedelta
from hashlib import md5

import requests
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

load_dotenv()

BASE_URL = os.environ["API_BASEURL"]

app = FastAPI(
    title="Basker API",
    description="API for Basker",
    version="0.1.0",
)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
