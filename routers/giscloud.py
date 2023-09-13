import json
import os
import re
from datetime import datetime

# from typing import Annotated,Dict
from urllib.request import Request

from dateutil import parser
from fastapi import APIRouter, Depends, HTTPException, Request

from dependencies import load_lms_token
from handlers import polygon_handler
from handlers.jsc_hanler import (
    AzureDbConnection,
    ConnectionSettings,
    Fixture,
    log_message,
)
from handlers.lms_requests import DeviceData, LMSRequest
from handlers.monday_handler import Coordinates, Item, MondayClient

router = APIRouter()
lms_base_url = os.getenv("LMS_API_BASEURL")
lms_request = LMSRequest(lms_base_url)
conn_settings = ConnectionSettings(
    server=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)
# db_conn.connect()


@router.post("/fixture")
async def update_lms(request):
    try:
        item_data = await request.json()
        # Extract relevant data from the incoming request payload
        new_fixture = DeviceData(
            serial_number=item_data.get("sn_nema"),
            pole=item_data.get("sn_nema"),
            latitude=item_data.get("latitude"),
            longitude=item_data.get("longitude"),
            id_gateway=14,
            # idIcon=2
        )
        old_sn = item_data.get("old_sn")
        session_site = lms_request.session("Or Yehuda - Israel")
        new_sn = lms_request.create_device(group_id=259, device_data=new_fixture.to_json())
        old_sn_res = lms_request.delete_device(group_id=259, serial_number=old_sn)
        # result = db_conn.delete_fixture(fixture_name=old_sn)
        return {"session_site": session_site, "new_sn": new_sn, "old_sn": old_sn_res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/sites")
def get_sites():
    # result = lms_request.sites()
    session_site = lms_request.session("Or Yehuda - Israel")
    new_fixture = DeviceData(
        serial_number="10344104",
        pole="10344104",
        latitude="31.15323",
        longitude="34.12343",
        id_gateway=14,
    )
    new_sn = lms_request.create_device(group_id=259, device_data=new_fixture.to_json())
    # if session_site == "Session Successfully":
    all_groups = lms_request.get_all_groups()
    print(all_groups)
    return {"message": "Hello World", "session_site": session_site, "new_sn": new_sn}


@router.get("/sites/{site_id}")
def get_site(site_id: str):
    lms_request.session(site_id)
    session_site = lms_request.session("Or Yehuda - Israel")
    new_fixture = DeviceData(
        serial_number="10344104",
        pole="10344104",
        latitude="31.15323",
        longitude="34.12343",
        id_gateway=14,
        # idIcon=2
    )
    new_sn = lms_request.create_device(group_id=259, device_data=new_fixture.to_json())


@router.post("/giscloud")
async def new_item(request: Request):
    # db_conn.connect()
    try:

        # request_dict = await  json.loads(request.body)
        # db_conn.connect()
        item_data_request = await request.json()
        log_message("New webhook request from giscloud", log_level="INFO")
        log_message(f"item_data_request: {item_data_request}", log_level="INFO")
        item_data = item_data_request.get("data")
        # Extract relevant data from the incoming request payload
        monday_handler = MondayClient(os.getenv("MONDAY_API_KEY"))
        sn_nema = item_data.get("sn_nema")
        sn_nema = get_regex_result(sn_nema)
        sn_type = define_barcode_type(sn_nema)
        # insertion_date = datetime.strptime(item_data.get("date"), "%Y-%m-%d %H:%M:%S")
        date_str = item_data.get("date")
        insertion_date = parser.isoparse(date_str)
        # insertion_date = datetime.strptime(item_data.get("date"), "%Y-%m-%dT%H:%M:%S%z")
        # insertion_date = datetime.strptime(item_data.get("date"), "%Y-%m-%dT%H:%M:%S%z")

        coordinates = Coordinates(
            long=float(item_data.get("longitude")),
            lat=float(item_data.get("latitude")),
        )
        picture = item_data.get("picture")
        picture_raw_data = item_data.get("raw_image")
        notes = item_data.get("note")
        old_sn = item_data.get("old_sn")
        old_sn = get_regex_result(old_sn)
        type_switch = item_data.get("type_switches")
        lamp_type = item_data.get("lamp_type")
        reason = item_data.get("svg")
        # Create an Item object based on the extracted data
        # take picture raw data from giscloud and send it to monday
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
        if sn_type == "Jnet1":
            new_fixture = DeviceData(
                pole=sn_nema, serial_number=sn_nema, latitude=coordinates.lat, longitude=coordinates.long, id_gateway=14
            )
            try:
                session_site = lms_request.session("Or Yehuda - Israel")
                new_sn = lms_request.create_device(group_id=259, device_data=new_fixture.to_json())
                if new_sn == "duplicate entry, you can not insert records that already exist":
                    new_sn = lms_request.update_device(
                        group_id=259, device_data=new_fixture.to_json(), serial_number=new_fixture.get_serial_number()
                    )
                    log_message(f"Fixture {sn_nema} updated successfully to LMS", log_level="INFO")
                else:
                    log_message(f"Fixture {sn_nema} inserted successfully to LMS", log_level="INFO")
                log_message(f"Fixture info: {new_fixture.to_json()}", log_level="INFO")
                # Only if sn_nema is not None
                if old_sn is not None:
                    try:
                        old_sn_res = lms_request.delete_device(group_id=259, serial_number=old_sn)
                        log_message(f"Fixture {old_sn} deleted successfully from LMS", log_level="INFO")
                    except Exception as e:
                        log_message(f"Failed to delete fixture {old_sn} from LMS: {e}", log_level="ERROR")
                        raise HTTPException(status_code=500, detail=str(e)) from e
                # lms_request.update_device
                return {
                    "LMS result": "Item added to LMS",
                    "new_sn": new_sn,
                    "old_sn": old_sn_res,
                    "Monday message": "Item added to Monday.com",
                    "item_id": item_id,
                    "delete old fixture": "fixture deleted successfully",
                    "fixture_sn": old_sn,
                }

            except Exception as e:
                log_message(f"Failed to insert fixture {sn_nema} to LMS: {e}", log_level="ERROR")
                log_message(f"fixture info: {new_fixture.to_json()}", log_level="INFO")
                raise HTTPException(status_code=500, detail=str(e)) from e
        elif sn_type == "Jnet0":
            db_conn = AzureDbConnection(conn_settings)
            new_fixture = Fixture(
                name=sn_nema,
                latitude=coordinates.lat,
                longitude=coordinates.long,
                id_gateway=19,
                ident=polygon_handler.get_getway_id(lon=coordinates.long, lat=coordinates.lat)
                # gateway_id should be desided based on location using polygons layer
            )
            new_device = DeviceData(
                serial_number=sn_nema,
                pole=sn_nema,
                latitude=coordinates.lat,
                longitude=coordinates.long,
                id_gateway=19,
            )
            try:
                if db_conn.fixture_exists(sn_nema):
                    fixture_id_res = db_conn.update_fixture(new_fixture, fixture_name=sn_nema)
                    device_res = lms_request.update_device(
                        group_id=259, device_data=new_device.to_json(), serial_number=new_device.get_serial_number()
                    )
                    log_message(f"Fixture {sn_nema} updated successfully", log_level="INFO")
                    log_message(f"Device {sn_nema} updated successfully: result = {device_res}", log_level="INFO")

                else:
                    fixture_id_res = db_conn.insert_fixture(new_fixture)
                    device_res = lms_request.create_device(group_id=259, device_data=new_device.to_json())
                    log_message(f"Fixture {sn_nema} inserted successfully", log_level="INFO")
                    log_message(f"Device {sn_nema} inserted successfully: result = {device_res}", log_level="INFO")
                log_message(f"Fixture info: {new_fixture.to_json()}", log_level="INFO")
            except Exception as e:
                db_conn.conn.rollback()

                log_message(f"Failed to insert fixture {sn_nema} to DB: {e}", log_level="ERROR")
                print(e)
            if old_sn is not None:
                try:
                    lms_request.delete_device(group_id=259, serial_number=old_sn)
                    db_conn.delete_fixture(fixture_name=old_sn)
                except Exception as e:
                    log_message(f"Failed to delete fixture {old_sn} from LMS or azure DB", log_level="ERROR")
                    raise HTTPException(status_code=500, detail=str(e)) from e

            db_conn.conn.commit()
            db_conn.disconnect()
            return {
                "Message": "Item added to LMS and Azure DB",
                "LMS result": lms_request,
                "JSC result": fixture_id_res,
                "Monday message": "Item added to Monday.com",
                "item_id": item_id,
                "delete old fixture": "fixture deleted successfully",
                "fixture_sn": old_sn,
            }
        else:
            log_message(f"Fixture {sn_nema} is not a Jnet fixture", log_level="Warning")
            return {
                "LMS result": "Item not added to LMS",
                "Monday message": "Item added to Monday.com",
                "item id": item_id,
                "delete old fixture": "fixture not been deleted",
                "old fixture sn": old_sn,
            }

    except Exception as e:
        log_message(f"An error occured: {str(e)}", log_level="ERROR")
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        log_message("End of webhook work from giscloud", log_level="INFO")


def get_regex_result(barcode: str) -> str:
    if barcode is not None:
        regex_result = re.search(r"([1-9][0-9]*\d{6,8})", barcode)
        return regex_result.group() if regex_result else barcode
    return barcode


def define_barcode_type(regex_result: str) -> str:
    if regex_result and regex_result.startswith("103"):
        return "Jnet1"
    elif regex_result and regex_result[:3] in ["402", "750", "220", "470", "200"]:
        return "Jnet0"
    else:
        return "Unknown"
