import os
import re
from logging import getLogger

from dateutil import parser
from fastapi import APIRouter, HTTPException, Request

from handlers import polygon_handler
from handlers.giscloud_handler import GisCloudHandler
from handlers.jsc_hanler import AzureDbConnection, ConnectionSettings, Fixture
from handlers.lms_requests import DeviceData, LMSRequest
from handlers.monday_handler import Coordinates, Item, MondayClient

logger = getLogger(__name__)

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


@router.post("/giscloud")
async def new_item(request: Request):
    # db_conn.connect()
    result = {}
    try:

        item_data_request = await request.json()
        logger.info("new webhook request from giscloud", extra={"item_data_request": item_data_request})
        item_data = item_data_request.get("data")
        gis_feature_id = item_data.get("ogc_fid")
        # Extract relevant data from the incoming request payload
        monday_handler = MondayClient(os.getenv("MONDAY_API_KEY"))
        sn_nema = item_data.get("sn_nema")
        sn_nema = get_regex_result(sn_nema)
        sn_type = define_barcode_type(sn_nema)
        date_str = item_data.get("date")
        insertion_date = parser.isoparse(date_str)

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
        layer_id = os.getenv("GIS_CLOUD_LAYER_ID")
        picture_raw_data = gis_handler.get_picture(layer_id=layer_id, feature_id=gis_feature_id, file_name=picture)

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
            webhook_response=result,
        )
        # Add the new item to Monday.com
        board_id = int(os.getenv("MONDAY_BOARD_ID"))
        group_id = os.getenv("MONDAY_GROUP_ID")

        if sn_type == "Jnet1":
            new_fixture = DeviceData(
                pole=sn_nema, serial_number=sn_nema, latitude=coordinates.lat, longitude=coordinates.long, id_gateway=14
            )
            try:
                lms_request.session("Or Yehuda - Israel")
                new_sn = lms_request.create_device(group_id=259, device_data=new_fixture.to_json())
                if new_sn == "duplicate entry, you can not insert records that already exist":
                    new_sn = lms_request.update_device(
                        group_id=259, device_data=new_fixture.to_json(), serial_number=new_fixture.get_serial_number()
                    )
                    logger.info("fixture updated successfully to LMS", extra={"new_sn": new_sn, sn_nema: sn_nema})
                    result["LMS result"] = f"{sn_nema} updated to LMS"
                else:
                    logger.info("fixture inserted successfully to LMS", extra={"new_sn": new_sn, sn_nema: sn_nema})
                    result["LMS result"] = f"{sn_nema} inserted to LMS"
                result["new_sn"] = new_sn
                result["fixture_info"] = new_fixture.to_json()
                logger.info("fixture info", extra={"fixture_info": new_fixture.to_json()})
                old_sn_res = None
                if old_sn is not None:
                    try:
                        old_sn_res = lms_request.delete_device(group_id=259, serial_number=old_sn)
                        logger.info("fixture deleted successfully from LMS", extra={"old_sn": old_sn})
                        result["delete old fixture"] = f"fixture {old_sn} deleted successfully"
                        result["old sn result"] = old_sn_res
                    except Exception as e:
                        logger.error("fixture not been deleted", exc_info=True, extra={"old_sn": old_sn})
                        result["delete old fixture"] = "fixture not been deleted"
                        result["error"] = str(e)
                        raise HTTPException(status_code=500, detail=str(e)) from e

            except Exception as e:
                logger.error(
                    "fixture has not been inserted",
                    exc_info=True,
                    extra={"sn_nema": sn_nema, "fixture_info": new_fixture.to_json()},
                )
                result["LMS result"] = f"Failed to insert fixture {sn_nema} to LMS: {e}"
                raise HTTPException(status_code=500, detail=str(e)) from e
        elif sn_type == "Jnet0":
            db_conn = AzureDbConnection(conn_settings)
            new_fixture = Fixture(
                name=sn_nema,
                latitude=coordinates.lat,
                longitude=coordinates.long,
                id_gateway=19,
                ident=polygon_handler.get_getway_id(lon=coordinates.long, lat=coordinates.lat),
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
                    logger.info("fixture updated successfully to azure DB", extra={"fixture_id_res": fixture_id_res})
                    device_res = lms_request.update_device(
                        group_id=259,
                        device_data=new_device.to_json(),
                        serial_number=new_device.get_serial_number(),
                    )
                    logger.info("fixture updated successfully to LMS", extra={"device_res": device_res})
                    result["JSC result"] = f"{sn_nema} updated to JSC, result = {fixture_id_res}"
                    result["LMS result"] = f"{sn_nema} updated to LMS, result = {device_res}"

                else:
                    fixture_id_res = db_conn.insert_fixture(new_fixture)
                    logger.info(
                        "fixture inserted successfully to azure DB",
                        extra={"fixture_id_res": fixture_id_res, "fixure_info": new_fixture.to_json()},
                    )
                    device_res = lms_request.create_device(group_id=259, device_data=new_device.to_json())
                    logger.info("fixture inserted successfully to LMS", extra={"device_res": device_res})
                    result["JSC result"] = f"{sn_nema} inserted to JSC, result = {fixture_id_res}"
                    result["LMS result"] = f"{sn_nema} inserted to LMS, result = {device_res}"
                result["fixture_info"] = new_fixture.to_json()
            except Exception as e:
                db_conn.conn.rollback()
                logger.error("failed to insert fixture", exc_info=True, extra={"fixture_info": new_fixture.to_json()})
                result["JSC result"] = f"Failed to insert fixture {sn_nema} to DB: {e}"
                print(e)
            if old_sn is not None:
                try:
                    lms_request.delete_device(group_id=259, serial_number=old_sn)
                    db_conn.delete_fixture(fixture_name=old_sn)
                    result["delete old fixture"] = f"fixture {old_sn} deleted successfully from JSC and LMS"
                except Exception as e:
                    logger.error("fixture not been deleted", exc_info=True, extra={"old_sn": old_sn})
                    result["delete old fixture"] = f"Failed to delete fixture {old_sn} from LMS or azure DB. Error: {e}"
                    raise HTTPException(status_code=500, detail=str(e)) from e

            db_conn.conn.commit()
            db_conn.disconnect()
            result["Status"] = "Pass"
            result["Message"] = "Item added to LMS and Azure DB"

        else:
            logger.warning("fixture is not a Jnet fixture", extra={"sn_nema": sn_nema})
            result["LMS result"] = f"Fixture {sn_nema} is not a Jnet fixture"
            result["Status"] = "Failed"
            result[
                "Message"
            ] = "Item Failed to added to LMS OR Azure DB, for more details check the log or the result fields"

    except Exception as e:
        logger.error("fixture not been inserted", exc_info=True, extra={"sn_nema": sn_nema})
        result["LMS result"] = f"An error occurred: {str(e)}"
        result["LMS result"] = f"Fixture {sn_nema} is not a Jnet fixture"
        result[
            "Status"
        ] = "Failed To enter the main process, check the log for more details and check carefully the request body"
        result[
            "Message"
        ] = "Item Failed to added to LMS OR Azure DB, for more details check the log or the result fields"
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        logger.info("giscloud webhook workflow has finished", extra={"result": result})
        if type_switch is not None and type_switch in LMS_groups.keys():
            relay_group_id = LMS_groups[type_switch]
            group_result = lms_request.associate_device_to_group(group_id=relay_group_id, serial_number=sn_nema)
            result["group associate result"] = group_result
        # test = lms_request.associate_device_to_group(group_id=286,serial_number=sn_nema)
        result["Monday message"] = "Item added to Monday.com"
        item_id = monday_handler.add_item(
            board_id=board_id,
            group_id=group_id,
            item=new_item,
        )
        result["item_id"] = item_id
        monday_handler.add_item_picture(item_id=item_id, image_raw_data=picture_raw_data)
        logger.info("giscloud webhook response", extra={"result": result})
        return result


def get_regex_result(barcode: str) -> str:
    if barcode is not None:
        regex_result = re.search(r"([1-9][0-9]*\d{6,8})", barcode)
        return regex_result.group() if regex_result else barcode
    return barcode


def define_barcode_type(regex_result: str) -> str:
    if regex_result and regex_result.startswith("103"):
        return "Jnet1"
    elif regex_result and regex_result[:3] in ["402", "750", "220", "470", "200", "400", "120"]:
        return "Jnet0"
    else:
        return "Unknown"


LMS_groups = {
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
