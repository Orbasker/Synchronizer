import datetime
import json
import logging

from handlers.firestore_handler import FirestoreHandler
from handlers.giscloud_handler import GisCloudHandler
from handlers.monday_handler import MondayClient,Item,Coordinates

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

conf = json.load(
    open('.env')
)

if __name__ == '__main__':
    state_handler = FirestoreHandler(
        cred=conf['FIREBASE']['CREDENTIALS'],
    )

    gis_handler = GisCloudHandler(
        api_key=conf['GIS_CLOUD']['API_KEY'],
    )
    monday_handler = MondayClient(
        api_key=conf['MONDAY']['API_KEY'],
    )

    logging.info('Getting GIS data')
    sns = gis_handler.get_sns_by_layer_id(
        layer_id=conf['GIS_CLOUD']['LAYER_ID'],
    )

    logging.info(f'fetching state records')
    state_records = state_handler.get_all_records()
    state_records_ids = [record['sn_nema'] for record in state_records]

    sn_to_check = set()
    
    for sn in sns:
        sn_data = sn['data']
        
        logging.info(f'Working on sn-{sn_data["sn_nema"]}')            
        if not sn_data['sn_nema'] in state_records_ids:
            sn_coordinates = Coordinates(
                long=sn_data['longitude'],
                lat=sn_data['latitude'],
            )

            item = Item(
                sn_nema=sn_data['sn_nema'],
                insertion_date=sn_data['date'],
                coordinates=sn_coordinates,
                picture=sn_data['picture'],
                picture_raw_data=sn_data['raw_image'],
                notes=sn_data['note'],
                old_sn=sn_data['old_sn'],
                type_switch=sn_data['type_switches'],
                lamp_type=sn_data['lamp_type']

            )

            logging.info('Adding item to Monday.com')

            item_id = monday_handler.add_item(
                board_id=conf['MONDAY']['BOARD_ID'],
                group_id='topics',
                item=item,
            ).strip()

            logging.info(f'Adding picture to item number {item_id}')

            monday_handler.add_item_picture(
                item_id=item_id,
                image_raw_data=item.picture_raw_data,
            )

            logging.info('Adding record to Firestore state')
            sn_data['item_id'] = item_id
            state_handler.add_record(sn_data)
            state_records_ids.append(sn_data['sn_nema'])
        else:
            logging.warning('ID already exists in state, adding to check later')
            sn_to_check.add(sn_data['sn_nema'])
            # logging.warning('ID already exists in state, checking if newer')
            # #TODO: Fix here
            # state_records = state_handler.get_all_records()
            # for record in state_records:
            #     if record['sn_nema'] == sn_data['sn_nema']:
            #         state_record = record
            #         state_record_date = datetime.datetime.fromtimestamp(
            #             record['date'].timestamp()
            #         )
            #         break

            # new_fetched_date = sn_data['date']

            # if new_fetched_date > state_record_date:
            #     logging.warning('Fetched record is newer! updating state')
            #     state_handler.update_record(
            #         old_record=state_record,
            #         new_record=sn_data,
            #     )
            #     sn_coordinates = Coordinates(
            #         long=sn_data['longitude'],
            #         lat=sn_data['latitude'],
            #     )
            #     logging.info('Update record in monday.com.')
            #     new_item = Item(
            #         sn_nema=sn_data['sn_nema'],
            #         insertion_date=sn_data['date'],
            #         coordinates=sn_coordinates,
            #         picture=sn_data['picture'],
            #         notes=sn_data['note'],
            #         old_sn=sn_data['old_sn'],
            #         type_switch=sn_data['type_switches'],
            #         lamp_type=sn_data['lamp_type'],
            #         _id=state_record['item_id'],
            #     )
            #     monday_handler.update_item(
            #         board_id=conf['MONDAY']['BOARD_ID'],
            #         new_item=new_item
            #     )
            #     logging.info(f'Item {new_item.id} updated successfully')
                
    logging.info('Done!')
