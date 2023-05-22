import os
from hashlib import md5

import requests
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from datetime import datetime, timedelta
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


@app.post("/token")
def token(
        username: str = os.environ["API_USERNAME"],
        password: str = os.environ["API_PASSWORD"],
):
    url = f"{BASE_URL}/token"
    hashed_password = md5(password.encode()).hexdigest()
    data = f'grant_type=password&username={username}&password={hashed_password}&client_id=ngAuthApp'
    return requests.post(
        url=url,
        data=data
    ).json()


@app.get("/sites")
def sites():
    url = f"{BASE_URL}/led/sites"
    return requests.get(
        url=url,
        headers={
            "Authorization": f"Bearer {token()['access_token']}"
        }
    ).json()


@app.post("/session")
def session(site_name: str = "Jerusalem - Israel"):
    url = f"{BASE_URL}/led/sites/{site_name}/session"
    res = requests.post(
        url=url,
        headers={
            "Authorization": f"Bearer {token()['access_token']}"
        }
    )

    if res.ok:
        return {
            "status": "ok",
        }

    res.raise_for_status()


@app.post("/turn_on")
def turn_on(
        level: int = 100,
        sn: int = 10315004,
):
    url = f"{BASE_URL}/led/devices/{sn}/commands/42"
    res =  requests.post(
        url=url,
        headers={
            "Authorization": f"Bearer {token()['access_token']}"
        },
        json={
            "arg1": level,
            "arg2": None,
            "arg3": None,
            "arg4": None,
            "arg5": None,
            "arg6": None,
            "arg7": None,
            "arg8": None,
            "arg9": None,
            "arg10": None,
            "arg11": None,
            "arg12": None,
            "arg13": None,
            "arg14": None,
            "arg15": None,
            "arg16": None
        }
    )
    if res.ok:
        device = res.json()['device']
        last_rx = device['lastRX']
        dt = datetime.strptime(last_rx, '%m/%d/%Y %I:%M:%S %p')
        now = datetime.now() - timedelta(hours=1)
        if (now - dt).seconds < 10:
            return {
                "status": "ok",
            }



if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)