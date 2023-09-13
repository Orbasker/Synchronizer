import re
from datetime import datetime
from urllib.parse import urljoin

import requests


class GisCloudHandler:
    def __init__(self, api_key):
        self._base_api_url = "https://api.giscloud.com/"
        self._images_base_api_url = "https://editor.giscloud.com/"
        self.api_key = api_key

    def get_picture(self, layer_id, feature_id, file_name):
        get_picture_data_url = urljoin(
            self._images_base_api_url, f"/rest/1/layers/{layer_id}/features/{feature_id}/picture/{file_name}"
        )
        return requests.get(
            url=get_picture_data_url,
            params={
                "api_key": self.api_key,
            },
        )._content

    def get_sn_picture_data(self, item: dict, layer_id, feature_id):
        file_name = item["data"]["picture"]
        get_picture_data_url = urljoin(
            self._images_base_api_url, f"/rest/1/layers/{layer_id}/features/{feature_id}/picture/{file_name}"
        )
        item["data"].update(
            {
                "raw_image": requests.get(
                    url=get_picture_data_url,
                    params={
                        "api_key": self.api_key,
                    },
                )._content
            }
        )
        return item["data"]["raw_image"]

    def get_sns_by_layer_id(self, layer_id):
        endpoint = urljoin(self._base_api_url, f"/1/layers/{layer_id}/features.json")
        layers = requests.get(url=endpoint, params={"api_key": self.api_key}).json()["data"]

        for item in layers:
            sn_nema = item["data"]["sn_nema"]
            date_raw_str = item["data"]["date"]
            if date_raw_str is None:
                date_str = "2021-01-01T00:00:00"
            else:
                date_str = date_raw_str.split(".")[0] if "." in date_raw_str else date_raw_str.split("+")[0]
            item["data"]["date"] = datetime.strptime(
                date_str,
                "%Y-%m-%dT%H:%M:%S",
            )
            gis_handler = GisCloudHandler(self.api_key)
            item["picture_data_raw"] = gis_handler.get_sn_picture_data(
                item=item, layer_id=layer_id, feature_id=item["__id"]
            )
            if sn_nema is not None:
                regex_result = re.search(r"([1-9][0-9]*\d{6,8})", sn_nema)
                item["data"]["sn_nema"] = regex_result.group() if regex_result else sn_nema

            yield item
