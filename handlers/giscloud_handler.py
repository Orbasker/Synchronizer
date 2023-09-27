from urllib.parse import urljoin

import requests


class GisCloudHandler:
    BASE_API_URL = "https://api.giscloud.com/"
    PICTURES_BASE_API_URL = "https://editor.giscloud.com/"

    def __init__(self, api_key):
        self._base_api_url = self.BASE_API_URL
        self._pictures_base_api_url = self.PICTURES_BASE_API_URL
        self.api_key = api_key

    def get_picture(self, layer_id, feature_id, file_name) -> bytes:
        get_picture_data_url = urljoin(
            self._pictures_base_api_url,
            f"/rest/1/layers/{layer_id}/features/{feature_id}/picture/{file_name}",
        )

        return requests.get(
            url=get_picture_data_url,
            params={
                "api_key": self.api_key,
            },
        ).content
