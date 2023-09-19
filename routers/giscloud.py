import os
import re
from dataclasses import dataclass
from datetime import datetime
from logging import getLogger

from dateutil import parser
from fastapi import APIRouter, HTTPException, Request
from requests.exceptions import HTTPError

from handlers import polygon_handler
from handlers.giscloud_handler import GisCloudHandler
from handlers.jsc_hanler import AzureDbConnection, ConnectionSettings, Fixture
from handlers.lms_requests import DeviceData, LMSRequest
from handlers.monday_handler import Coordinates, MondayClient, MondayItem

logger = getLogger("giscloud")

router = APIRouter()


lms_base_url = os.getenv("LMS_API_BASEURL")
lms_request = LMSRequest(lms_base_url)
gis_handler = GisCloudHandler(os.getenv("GIS_CLOUD_API_KEY"))

conn_settings = ConnectionSettings(
    server=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)

LMS_GROUPS = {
    "Illuminated flag": 286,
    "grilanda": 284,
    "Pedestrian sign": 282,
    "tree switches": 280,
    "Or Yehuda Garden Flood": 288,
    "roundabout button": 283,
    "Logo sign": 285,
    "football switches": 346,
    "24/7 sign": 372,
    "V-led": 369,
}


@dataclass
class GisItem:
    feature_id: int
    sn_nema: str
    datetime: datetime
    coordinate: Coordinates
    picture: str
    note: str
    old_sn: str
    type_switches: str
    lamp_type: str
    reason: str
    jnet_type: str


async def extract_gis_item(req: Request) -> GisItem:
    request_body = await req.json()

    if "data" not in request_body:
        raise HTTPException(status_code=400, detail="Invalid request body")

    logger.info("extracting gis item from request body", extra={"request_body": request_body})

    data = request_body["data"]
    sn_nema = extract_sn_nema_from_barcode(data["sn_nema"])

    return GisItem(
        jnet_type=assign_jnet_type(sn_nema),
        feature_id=int(data["ogc_fid"]),
        sn_nema=sn_nema,
        old_sn=extract_sn_nema_from_barcode(data["old_sn"]),
        datetime=parser.isoparse(data["date"]),
        coordinate=Coordinates(
            long=float(data["longitude"]),
            lat=float(data["latitude"]),
        ),
        picture=data["picture"],
        note=data["note"],
        type_switches=data["type_switches"],
        lamp_type=data["lamp_type"],
        reason=data["svg"],
    )


def handle_jnet_1(gis_item: GisItem) -> dict:
    new_fixture = DeviceData(
        pole=gis_item.sn_nema,
        serial_number=gis_item.sn_nema,
        latitude=gis_item.coordinate.lat,
        longitude=gis_item.coordinate.long,
        id_gateway=14,
    )
    lms_request.session("Or Yehuda - Israel")
    new_fixture_json = new_fixture.to_json()

    new_sn = lms_request.create_device(
        group_id=259,
        device_data=new_fixture_json,
    )

    results = {}

    if new_sn == "duplicate entry, you can not insert records that already exist":
        logger.info("fixture already exists in LMS", extra={"sn_nema": gis_item.sn_nema})

        try:
            new_sn = lms_request.update_device(
                group_id=259,
                device_data=new_fixture_json,
                serial_number=new_fixture.get_serial_number(),
            )
            logger.info("fixture updated successfully to LMS", extra={"new_sn": new_sn, "sn_nema": gis_item.sn_nema})
            results["LMS result"] = f"{gis_item.sn_nema} updated to LMS"
        except HTTPError:
            logger.error(
                "fixture has not been updated",
                exc_info=True,
                extra={"sn_nema": gis_item.sn_nema, "fixture_info": new_fixture_json},
            )
            results["LMS result"] = f"failed to insert fixture {gis_item.sn_nema}"

    else:
        logger.info("fixture inserted successfully to LMS", extra={"new_sn": new_sn, "sn_nema": gis_item.sn_nema})
        results["LMS result"] = f"{gis_item.s} inserted to LMS"

    results["new_sn"] = new_sn
    results["fixture_info"] = new_fixture_json
    logger.info("fixture info", extra={"fixture_info": new_fixture_json})

    if gis_item.old_sn:
        try:
            old_sn_res = lms_request.delete_device(group_id=259, serial_number=gis_item.old_sn)
            logger.info("fixture deleted successfully from LMS", extra={"old_sn": gis_item.old_sn})
            results["delete old fixture"] = f"fixture {gis_item.old_sn} deleted successfully"
            results["old sn result"] = old_sn_res
        except Exception as e:
            logger.error("fixture not been deleted", exc_info=True, extra={"old_sn": gis_item.old_sn})
            results["delete old fixture"] = "fixture not been deleted"
            results["error"] = str(e)
            raise HTTPException(status_code=500) from e

    if gis_item.type_switches in LMS_GROUPS.keys():
        relay_group_id = LMS_GROUPS[gis_item.type_switch]
        group_result = lms_request.associate_device_to_group(group_id=relay_group_id, serial_number=gis_item.sn_nema)
        results["group associate result"] = group_result

    return results


def handle_jnet_0(gis_item: GisItem) -> dict:
    db_conn = AzureDbConnection(conn_settings)
    new_fixture = Fixture(
        name=gis_item.sn_nema,
        latitude=gis_item.coordinate.lat,
        longitude=gis_item.coordinate.long,
        id_gateway=19,
        ident=polygon_handler.get_getway_id(
            lon=gis_item.coordinate.long,
            lat=gis_item.coordinate.lat,
        ),
    )
    new_device = DeviceData(
        serial_number=gis_item.sn_nema,
        pole=gis_item.sn_nema,
        latitude=gis_item.coordinate.lat,
        longitude=gis_item.coordinate.long,
        id_gateway=19,
    )
    fixture_dict = new_fixture.to_dict()
    try:
        results = {}
        if db_conn.fixture_exists(gis_item.sn_nema):
            fixture_id_res = db_conn.update_fixture(new_fixture, fixture_name=gis_item.sn_nema)
            logger.info("fixture updated successfully to azure DB", extra={"fixture_id_res": fixture_id_res})
            device_res = lms_request.update_device(
                group_id=259,
                device_data=new_device.to_json(),
                serial_number=new_device.get_serial_number(),
            )
            results["LMS result"] = f"{gis_item.sn_nema} updated to LMS, result = {device_res}"
            logger.info("fixture updated successfully to LMS", extra={"device_res": device_res})
        else:
            fixture_id_res = db_conn.insert_fixture(new_fixture)
            results["JSC result"] = f"{gis_item.sn_nema} inserted to JSC, result = {fixture_id_res}"
            logger.info(
                "fixture inserted successfully to azure DB",
                extra={"fixture_id_res": fixture_id_res, "fixure_info": fixture_dict},
            )
            device_res = lms_request.create_device(group_id=259, device_data=new_device.to_json())
            logger.info("fixture inserted successfully to LMS", extra={"device_res": device_res})
            results["LMS result"] = f"{gis_item.sn_nema} inserted to LMS, result = {device_res}"
        results["fixture_info"] = new_fixture.to_json()
    except Exception as e:
        db_conn.conn.rollback()
        logger.error("failed to insert fixture", exc_info=True, extra={"fixture_info": fixture_dict})
        results["JSC result"] = f"Failed to insert fixture {gis_item.sn_nema} to DB: {e}"
    if gis_item.old_sn:
        try:
            lms_request.delete_device(group_id=259, serial_number=gis_item.old_sn)
            db_conn.delete_fixture(fixture_name=gis_item.old_sn)
            results["delete old fixture"] = f"fixture {gis_item.old_sn} deleted successfully from JSC and LMS"
        except Exception as e:
            logger.error("fixture not been deleted", exc_info=True, extra={"old_sn": gis_item.old_sn})
            results[
                "delete old fixture"
            ] = f"Failed to delete fixture {gis_item.old_sn} from LMS or azure DB. Error: {e}"
            raise e

    db_conn.conn.commit()
    db_conn.disconnect()
    results["Status"] = "Pass"
    results["Message"] = "Item added to LMS and Azure DB"
    return results


def extract_sn_nema_from_barcode(barcode: str) -> str:
    if barcode is not None:
        regex_result = re.search(r"([1-9][0-9]*\d{6,8})", barcode)
        return regex_result.group() if regex_result else barcode
    return barcode


def assign_jnet_type(regex_result: str) -> str:
    if regex_result and regex_result.startswith("103"):
        return "Jnet1"
    elif regex_result and regex_result[:3] in ["402", "750", "220", "470", "200", "400", "120"]:
        return "Jnet0"
    else:
        return "Unknown"


@router.post("/giscloud")
async def new_item(request: Request):
    results = {}
    logger.info("new webhook request from giscloud")
    gis_item = await extract_gis_item(request)

    logger.info("initializing monday handler")
    monday_api_key = os.getenv("MONDAY_API_KEY")
    monday_handler = MondayClient(monday_api_key)

    picture_raw_data = gis_handler.get_picture(
        layer_id=os.getenv("GIS_CLOUD_LAYER_ID"),
        feature_id=gis_item.feature_id,
        file_name=gis_item.picture,
    )

    monday_item = MondayItem(
        sn_nema=gis_item.sn_nema,
        insertion_date=gis_item.datetime,
        coordinates=gis_item.coordinate,
        picture=gis_item.picture,
        picture_raw_data=picture_raw_data,
        notes=gis_item.note,
        old_sn=gis_item.old_sn,
        type_switch=gis_item.type_switches,
        lamp_type=gis_item.lamp_type,
        reason=gis_item.reason,
        webhook_response={},
    )

    board_id = int(os.getenv("MONDAY_BOARD_ID"))
    group_id = os.getenv("MONDAY_GROUP_ID")

    if gis_item.jnet_type == "Jnet1":
        logger.info("fixture type is a Jnet1", extra={"sn_nema": gis_item.sn_nema})
        results = handle_jnet_1(gis_item=gis_item)
    elif gis_item.jnet_type == "Jnet0":
        logger.info("fixture type is a Jnet0", extra={"sn_nema": gis_item.sn_nema})
        results = handle_jnet_0(gis_item=gis_item)
    else:
        logger.warning("fixture type is unknown", extra={"sn_nema": gis_item.sn_nema})
        results = {
            "LMS result": f"fixture {gis_item.sn_nema} is not a Jnet fixture",
            "Status": "Failed",
            "Message": "Item Failed to added to LMS OR Azure DB, for more details check the log or the result fields",
        }

    logger.info("giscloud webhook workflow has finished", extra={"results": results})

    return monday_handler.add_item(
        board_id=board_id,
        group_id=group_id,
        item=monday_item,
    )
