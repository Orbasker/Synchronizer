import os

from handlers.lms_requests import LMSRequest


async def load_lms_token():
    lms_base_url = os.getenv("LMS_API_BASEURL")
    return LMSRequest(lms_base_url)
