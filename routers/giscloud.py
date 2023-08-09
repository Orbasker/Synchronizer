import os
from datetime import datetime
from typing import Annotated, Type
from urllib.request import Request

from fastapi import APIRouter, Depends, HTTPException

from dependencies import load_lms_token
from handlers.lms_requests import DeviceData, LMSRequest
from handlers.monday_handler import Coordinates, Item, MondayClient

router = APIRouter()


@router.get("/sites")
def get_sites(lms: Annotated[LMSRequest, Depends(load_lms_token)]):
    result = lms.sites()
    session_site = lms.session(result[0]["company"])
    if session_site == "Session Successfully":
        all_groups = lms.get_all_groups()
        all_sns = lms.get_all_devices(all_groups[0]["id"])
        new_sn_data = DeviceData(
            pole="111111",
            latitude="31.1532",
            longitude="34.1234",
            id_gateway=1,
        )
        new_sn = lms.create_device(group_id=1, device_data=new_sn_data.to_json())
        return {"session_site": session_site, "all_groups": all_groups, "all_sns": all_sns, "new_sn": new_sn}
    return {"result": result, "message": "Hello World", "session_site": session_site}


@router.get("/sites/{site_id}")
def get_site(site_id: str, lms: Annotated[LMSRequest, Depends(load_lms_token)]):
    lms.session(site_id)


@router.post("/giscloud")
async def new_item(request: Type[Request]):
    try:
        item_data = await request.json()
        # Extract relevant data from the incoming request payload

        monday_handler = MondayClient(os.getenv("MONDAY_API_KEY"))
        sn_nema = item_data.get("sn_nema")
        insertion_date = datetime.strptime(item_data.get("date"), "%Y-%m-%d %H:%M:%S")
        coordinates = Coordinates(
            long=float(item_data.get("longitude")),
            lat=float(item_data.get("latitude")),
        )
        picture = item_data.get("picture")
        picture_raw_data = item_data.get("raw_image")
        notes = item_data.get("note")
        old_sn = item_data.get("old_sn")
        type_switch = item_data.get("type_switches")
        lamp_type = item_data.get("lamp_type")
        reason = item_data.get("svg")
        # Create an Item object based on the extracted data
        new_item = Item(
            sn_nema=sn_nema,
            insertion_date=insertion_date,
            coordinates=coordinates,
            picture=picture,
            picture_raw_data=picture_raw_data,
            notes=notes,
            old_sn=old_sn,
            type_switch=type_switch,
            lamp_type=lamp_type,
            reason=reason,
        )
        # Add the new item to Monday.com
        board_id = int(os.getenv("MONDAY_BOARD_ID"))
        group_id = os.getenv("MONDAY_GROUP_ID")
        item_id = monday_handler.add_item(
            board_id=board_id,
            group_id=group_id,
            item=new_item,
        )
        return {"message": "Item added to Monday.com", "item_id": item_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
