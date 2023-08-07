import json
import logging
import os
from datetime import timezone

from dotenv import load_dotenv

from handlers.firestore_handler import FirestoreHandler
from handlers.giscloud_handler import GisCloudHandler
from handlers.monday_handler import Coordinates, Item, MondayClient

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)s %(module)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def update_state_records(sns, state_records) -> None:
    state_records_ids = [record["sn_nema"] for record in state_records]
    for sn in sns:
        sn_data = sn["data"]

        logging.info(f'Working on sn-{sn_data["sn_nema"]}')
        if sn_data["sn_nema"] not in state_records_ids:
            sn_coordinates = Coordinates(
                long=sn_data["longitude"],
                lat=sn_data["latitude"],
            )

            item = Item(
                sn_nema=sn_data["sn_nema"],
                insertion_date=sn_data["date"],
                coordinates=sn_coordinates,
                picture=sn_data["picture"],
                picture_raw_data=sn_data["raw_image"],
                notes=sn_data["note"],
                old_sn=sn_data["old_sn"],
                type_switch=sn_data["type_switches"],
                lamp_type=sn_data["lamp_type"],
                reason=sn_data["svg"],
            )
            logging.info("Adding item to Fire store")
            state_handler.add_record(sn_data)
            state_records_ids.append(sn_data["sn_nema"])
        else:
            logging.warning("ID already exists in state")
            if old_record := state_handler.get_record_by_id(sn_data["sn_nema"]):
                logging.error("ID not found in state!")
                sn_date_offset_aware = sn_data["date"].replace(tzinfo=timezone.utc)
                if old_record["date"] >= sn_date_offset_aware:
                    logging.warning("Fetched record is older!")
                else:
                    logging.warning("Fetched record is newer! updating state")
                    state_handler.update_record(old_record=old_record, new_record=sn_data)


if __name__ == "__main__":
    state_handler = FirestoreHandler(
        cred={
            "type": os.getenv("FIRESTORE_TYPE"),
            "project_id": os.getenv("FIRESTORE_PROJECT_ID"),
            "private_key_id": os.getenv("FIRESTORE_PRIVATE_KEY_ID"),
            "private_key": os.getenv("FIRESTORE_PRIVATE_KEY").replace("\\n", "\n"),
        }
    )

    gis_handler = GisCloudHandler(
        api_key=os.getenv("GIS_CLOUD_API_KEY"),
    )
    monday_handler = MondayClient(
        api_key=os.getenv("MONDAY_API_KEY"),
    )

    logging.info("Getting GIS data")
    sns = gis_handler.get_sns_by_layer_id(
        layer_id=os.getenv("GIS_CLOUD_LAYER_ID"),
    )

    logging.info("fetching state records")
    state_records = state_handler.get_all_records()
    for sn in sns:
        logging.info(f'Working on sn-{sn["data"]["sn_nema"]}')
        sn_nema = sn["data"]["sn_nema"]
        if sn_nema and not state_handler.check_record_exists(sn_nema):
            logging.info("adding to Fire store")
            FirestoreHandler.add_record(state_handler, sn["data"])
            new_item = Item(
                sn_nema=sn["data"]["sn_nema"],
                insertion_date=sn["data"]["date"],
                coordinates=Coordinates(
                    long=sn["data"]["longitude"],
                    lat=sn["data"]["latitude"],
                ),
                picture=sn["data"]["picture"],
                picture_raw_data=sn["picture_data_raw"],
                notes=sn["data"]["note"],
                old_sn=sn["data"]["old_sn"],
                type_switch=sn["data"]["type_switches"],
                lamp_type=sn["data"]["lamp_type"],
                reason=sn["data"]["svg"],
            )
            logging.info("adding to Monday.com")
            response = monday_handler.add_item(
                board_id=os.getenv("MONDAY_BOARD_ID"),
                group_id=os.getenv("MONDAY_GROUP_ID"),
                item=new_item,
            )
            item_id = response
            new_record = sn["data"]
            new_record["item_id"] = item_id
            state_handler.update_record(old_record=sn["data"], new_record=new_record)
            monday_handler.add_item_picture(item_id=item_id, image_raw_data=sn["picture_data_raw"])
        else:
            logging.warning("ID already exists in state")
            if old_record := state_handler.get_record_by_id(sn["data"]["sn_nema"]):
                logging.error("ID not found in state!")
                sn_date_offset_aware = sn["data"]["date"].replace(tzinfo=timezone.utc)
                if old_record["date"] >= sn_date_offset_aware:
                    logging.warning("Fetched record is older!")
                else:
                    logging.warning("Fetched record is newer! updating state")
                    state_handler.update_record(old_record=old_record, new_record=sn["data"])
                    logging.info("updating Monday.com")
                    monday_handler.update_item(
                        board_id=os.getenv("MONDAY_BOARD_ID"),
                        new_item=Item(
                            sn_nema=sn["data"]["sn_nema"],
                            insertion_date=sn["data"]["date"],
                            coordinates=Coordinates(
                                long=sn["data"]["longitude"],
                                lat=sn["data"]["latitude"],
                            ),
                            picture=sn["data"]["picture"],
                            picture_raw_data=sn["data"]["raw_image"],
                            notes=sn["data"]["note"],
                            old_sn=sn["data"]["old_sn"],
                            type_switch=sn["data"]["type_switches"],
                            lamp_type=sn["data"]["lamp_type"],
                            reason=sn["data"]["svg"],
                            item_id=old_record["item_id"],
                        ),
                    )

    logging.info("Done!")
