import uvicorn
from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from starlette.responses import RedirectResponse

from dependencies import load_lms_token
from routers import giscloud

app = FastAPI(
    dependencies=[Depends(load_lms_token)],
    debug=True,
)

app.include_router(giscloud.router)


@app.on_event("startup")
async def startup_event():
    load_dotenv()


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=80,
    )
