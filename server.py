import uvicorn
from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from starlette.responses import RedirectResponse

from handlers.jsc_hanler import AzureDbConnection, ConnectionSettings, Fixture
from handlers.lms_requests import DeviceData, LMSRequest
from handlers.monday_handler import Coordinates, Item, MondayClient

app = FastAPI(
    dependencies=[Depends(load_lms_token)],
    debug=True,
)

lms_base_url = os.getenv("LMS_API_BASEURL")
lms_request = LMSRequest(lms_base_url)


@app.on_event("startup")
async def startup_event():
    load_dotenv()


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.post("/fixture")
async def update_lms(request: Request):
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


@app.get("/sites")
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
    # print(all_groups[)
    # all_sns = lms_request.get_all_devices(all_groups[0]["serialNumber"])
    # if new_fixture.pole not in all_sns:
    #     print("not in")
    # else:
    #     print("in")
    # print(all_sns)
    #     new_sn_data = DeviceData(
    #         pole="111111",
    #         latitude="31.1532",
    #         longitude="34.1234",
    #         id_gateway=1,
    #     )
    #     new_sn = lms_request.create_device(group_id=1, device_data=new_sn_data.to_json())
    #     return {"session_site": session_site, "all_groups": all_groups, "all_sns": all_sns, "new_sn": new_sn}
    return {"message": "Hello World", "session_site": session_site, "new_sn": new_sn}


@app.get("/sites/{site_id}")
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


@app.post("/giscloud")
async def new_item(request: Request):
    try:
        item_data = await request.json().get("data")
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

        try:
            new_fixture = Fixture(
                name=sn_nema,
                latitude=coordinates.lat,
                longitude=coordinates.long,
                id_gateway=14,
            )
            if db_conn.fixture_exists(sn_nema):
                fixture_id_res = db_conn.update_fixture(new_fixture, fixture_name=sn_nema)
            else:
                fixture_id_res = db_conn.insert_fixture(new_fixture)
            db_conn.delete_fixture(fixture_name=old_sn)

            return {
                "LMS result": "Item added to LMS",
                "id": fixture_id_res,
                "Monday message": "Item added to Monday.com",
                "item_id": item_id,
                "delete old fixture": "fixture deleted successfully",
                "fixture_id": old_sn,
            }

        except Exception as e:
            print(e)
        finally:
            db_conn.disconnect()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=80,
    )
