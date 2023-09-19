import os
from hashlib import md5

import requests
from dotenv import load_dotenv
from pydantic import HttpUrl

load_dotenv()


class DeviceData:
    def __init__(
        self,
        pole=None,
        latitude=None,
        longitude=None,
        serial_number=None,
        id_gateway=None,
        id_type=1,
    ):
        self.pole = pole
        self.latitude = latitude
        self.longitude = longitude
        self.serialNumber = serial_number
        self.idGateway = id_gateway
        self.idType = id_type

    def to_json(self):
        return {
            "pole": self.pole,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "serialNumber": self.serialNumber,
            "idGateway": self.idGateway,
            "idType": self.idType,
        }

    def set_pole(self, pole):
        self.pole = pole

    def get_pole(self):
        return self.pole

    def set_latitude(self, latitude):
        self.latitude = latitude

    def get_latitude(self):
        return self.latitude

    def set_longitude(self, longitude):
        self.longitude = longitude

    def get_longitude(self):
        return self.longitude

    def set_serial_number(self, serial_number):
        self.serialNumber = serial_number

    def get_serial_number(self):
        return self.serialNumber

    def set_id_gateway(self, id_gateway):
        self.idGateway = id_gateway

    def get_id_gateway(self):
        return self.idGateway

    def set_id_type(self, id_type):
        self.idType = id_type

    def get_id_type(self):
        return self.idType


class LMSRequest:
    def __init__(self, base_url):
        self.BASE_URL = base_url
        self.token = self.get_access_token()

    def get_access_token(self):
        url = f"{self.BASE_URL}/token"
        username = os.getenv("LMS_API_USERNAME")
        password = os.getenv("LMS_API_PASSWORD")
        hashed_password = md5(password.encode()).hexdigest()
        data = f"grant_type=password&username={username}&password={hashed_password}&client_id=ngAuthApp"
        response = requests.post(url=url, data=data)
        response.raise_for_status()
        return response.json()["access_token"]

    def make_authenticated_request(
        self,
        url: HttpUrl,
        method: str,
        json_data: dict = None,
    ):
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=json_data or None,
        )
        response.raise_for_status()
        try:
            return response.json()
        except Exception:
            return response

    def get_all_groups(self):
        url = f"{self.BASE_URL}/led/groups"
        return self.make_authenticated_request(url, "GET")

    def get_group_by_id(self, group_id):
        url = f"{self.BASE_URL}/led/groups/{group_id}"
        return self.make_authenticated_request(url, "GET")

    def sites(self):
        url = f"{self.BASE_URL}/led/sites"
        return self.make_authenticated_request(url, "GET")

    def session(self, site_name: str = "Jerusalem - Israel"):
        url = f"{self.BASE_URL}/led/sites/{site_name}/session"
        return self.make_authenticated_request(url, "POST")

    def turn_on(
        self,
        level: int = 100,
        sn: int = 10315004,
    ):
        url = f"{self.BASE_URL}/led/devices/{sn}/commands/42"
        json_data = {
            "arg1": level,
            "arg2": None,
            "arg3": None,
            "arg4": None,
            "arg5": None,
            "arg6": None,
            "arg7": None,
            "arg8": None,
            "arg9": None,
            "arg10": None,
            "arg11": None,
            "arg12": None,
            "arg13": None,
            "arg14": None,
            "arg15": None,
            "arg16": None,
        }
        return self.make_authenticated_request(url, "POST", json_data)

    def logout(self, site_name: str = "Jerusalem - Israel"):
        url = f"{self.BASE_URL}/led/sites/{site_name}/logout"
        return self.make_authenticated_request(url, "POST")

    def create_group(
        self,
        name: str,
        parent_group_id: int = None,
        id_network_type: int = 2,
        id_device_type: int = 1,
        allow_children: int = 0,
    ):
        url = f"{self.BASE_URL}/led/groups"
        json_data = {
            "name": name,
            "parentGroupId": parent_group_id,
            "idNetworkType": id_network_type,
            "idDeviceType": id_device_type,
            "allowChildren": allow_children,
        }
        return self.make_authenticated_request(url, "POST", json_data)

    def update_group(
        self,
        group_id: int,
        name: str,
        parent_group_id: int = None,
        id_network_type: int = 2,
        id_device_type: int = 1,
        allow_children: int = 0,
    ):
        url = f"{self.BASE_URL}/led/groups/{group_id}"
        json_data = {
            "name": name,
            "parentGroupId": parent_group_id,
            "idNetworkType": id_network_type,
            "idDeviceType": id_device_type,
            "allowChildren": allow_children,
        }
        return self.make_authenticated_request(url, "PUT", json_data)

    def delete_group(self, group_id: int):
        url = f"{self.BASE_URL}/led/groups/{group_id}"
        response = requests.delete(url, headers={"Authorization": f"Bearer {self.token}"})
        if response.status_code == 200:
            return "Group deleted successfully."
        elif response.status_code == 400 and "could not be deleted. The group has devices associated." in response.text:
            return "Group could not be deleted. The group has devices associated."
        else:
            response.raise_for_status()

    def get_all_devices(self, group_id):
        url = f"{self.BASE_URL}/led/groups/{group_id}/devices"
        return self.make_authenticated_request(url, "GET")

    def get_device_by_serial(self, group_id, serial_number):
        url = f"{self.BASE_URL}/led/groups/{group_id}/devices/{serial_number}"
        response = self.make_authenticated_request(url, "GET")
        return response.json()

    def create_device(self, group_id, device_data):
        url = f"{self.BASE_URL}/led/groups/{group_id}/devices"
        return self.make_authenticated_request(
            url=url,
            method="POST",
            json_data=device_data,
        )

    def update_device(self, group_id, serial_number, device_data):
        # asosicate = self.associate_device_to_group(group_id=259, serial_number=serial_number, associate=0)
        # asosicate.raise_for_status()
        url = f"{self.BASE_URL}/led/groups/{group_id}/devices/{serial_number}"
        return self.make_authenticated_request(url, "PUT", json_data=device_data)
        # return response.json()

    def delete_device(self, group_id, serial_number):
        if serial_number == "":
            return "Serial number is empty."
        url = f"{self.BASE_URL}/led/groups/{group_id}/devices/{serial_number}"
        response = self.make_authenticated_request(url, "DELETE")
        if response.status_code == 200:
            return "Device deleted successfully."
        return "Device could not be deleted."

    def associate_device_to_group(self, group_id, serial_number, associate=0):
        url = f"{self.BASE_URL}/led/groups/{group_id}/devices/{serial_number}?associate={associate}"
        return self.make_authenticated_request(url, "POST")

    def get_all_types(self):
        return self._extracted_from_get_all_light_profiles_2("/led/type")

    def get_type_by_id(self, type_id):
        return self._extracted_from_get_light_profile_2("/led/type/", type_id)

    def create_gateway(
        self,
        name,
        ident,
        latitude,
        longitude,
        id_network_type=None,
        mac_address=None,
    ):
        url = f"{self.BASE_URL}/led/gateways"
        data = {
            "name": name,
            "ident": ident,
            "latitude": latitude,
            "longitude": longitude,
            "idNetworkType": id_network_type,
            "macAddress": mac_address,
        }
        response = self.make_authenticated_request(url, "POST", json_data=data)
        return response.json()

    def get_all_gateways(self):
        return self._extracted_from_get_all_light_profiles_2("/led/gateways")

    def get_gateway_by_id(self, id_gateway):
        return self._extracted_from_get_light_profile_2("/led/gateways/", id_gateway)

    def update_gateway(
        self,
        id_gateway,
        name,
        ident,
        latitude,
        longitude,
        id_network_type=None,
        mac_address=None,
    ):
        url = f"{self.BASE_URL}/led/gateways/{id_gateway}"
        data = {
            "name": name,
            "ident": ident,
            "latitude": latitude,
            "longitude": longitude,
            "idNetworkType": id_network_type,
            "macAddress": mac_address,
        }
        response = self.make_authenticated_request(url, "PUT", json=data)
        return response.json()

    def get_all_commands(self):
        return self._extracted_from_get_all_light_profiles_2("/led/commands")

    def get_command_by_id(self, idCommand):
        return self._extracted_from_get_light_profile_2("/led/commands/", idCommand)

    def send_group_command(self, group_id, opcode, arg1=None):
        return self._extracted_from_send_gateway_command_2("/led/groups/", group_id, opcode, arg1)

    def send_device_command(self, serial_number, opcode, arg1=None):
        return self._extracted_from_send_gateway_command_2("/led/devices/", serial_number, opcode, arg1)

    def send_gateway_command(self, gateway_id, opcode, arg1=None):
        return self._extracted_from_send_gateway_command_2("/led/gateways/", gateway_id, opcode, arg1)

    # TODO Rename this here and in `send_group_command`, `send_device_command` and `send_gateway_command`
    def _extracted_from_send_gateway_command_2(self, arg0, arg1, opcode):
        url = f"{self.BASE_URL}{arg0}{arg1}/commands/{opcode}"
        data = {}
        if arg1 is not None:
            data["arg1"] = arg1
        response = self.make_authenticated_request(url, "POST", json=data)
        return response.json()

    def create_light_profile(self, name, typeLP, events):
        url = f"{self.BASE_URL}/led/profiles"
        data = {"name": name, "typeLP": typeLP, "events": events}
        response = self.make_authenticated_request(url, "POST", json=data)
        return response.json()

    def get_all_light_profiles(self):
        return self._extracted_from_get_all_light_profiles_2("/led/profiles")

    # TODO Rename this here and in `get_all_types`, `get_all_gateways`, `get_all_commands` and `get_all_light_profiles`
    def _extracted_from_get_all_light_profiles_2(self, arg0):
        url = f"{self.BASE_URL}{arg0}"
        response = self.make_authenticated_request(url, "GET")
        return response.json()

    def get_light_profile(self, idLP):
        return self._extracted_from_get_light_profile_2("/led/profiles/", idLP)

    # TODO Rename this here and in `get_type_by_id`, `get_gateway_by_id`, `get_command_by_id` and `get_light_profile`
    def _extracted_from_get_light_profile_2(self, arg0, arg1):
        url = f"{self.BASE_URL}{arg0}{arg1}"
        response = self.make_authenticated_request(url, "GET")
        return response.json()

    def update_light_profile(self, idLP, name, typeLP, events):
        url = f"{self.BASE_URL}/led/profiles/{idLP}"
        data = {"name": name, "typeLP": typeLP, "events": events}
        response = self.make_authenticated_request(url, "PUT", json=data)
        return response.json()

    def delete_light_profile(self, idLP):
        url = f"{self.BASE_URL}/led/profiles/{idLP}"
        response = self.make_authenticated_request(url, "DELETE")
        return response.status_code

    def associate_light_profile_to_group(self, idLP, idGroup):
        url = f"{self.BASE_URL}/led/profiles/{idLP}/groups/{idGroup}"
        return self._extracted_from_get_devices_by_group_3(url, "POST")

    def get_light_profiles_associated_to_groups(self):
        url = f"{self.BASE_URL}/led/profiles/groups"
        return self._extracted_from_get_devices_by_group_3(url, "GET")

    def reassociate_light_profile_to_group(self, idLP, idGroup):
        url = f"{self.BASE_URL}/led/profiles/{idLP}/groups/{idGroup}"
        return self._extracted_from_get_devices_by_group_3(url, "PUT")

    def delete_associated_light_profile_from_group(self, idLP, idGroup):
        url = f"{self.BASE_URL}/led/profiles/{idLP}/groups/{idGroup}"
        return self._extracted_from_get_devices_by_group_3(url, "DELETE")

    def get_device_credentials(self, base_url):
        url = f"{base_url}/led/devices/credentials"
        return self._extracted_from_get_devices_by_group_3(url, "GET")

    def get_devices_by_group(self, base_url, id_group):
        url = f"{base_url}/led/groups/{id_group}/devicelist"
        return self._extracted_from_get_devices_by_group_3(url, "GET")

    # TODO Rename this here and in `associate_light_profile_to_group`, `get_light_profiles_associated_to_groups`, `reassociate_light_profile_to_group`, `delete_associated_light_profile_from_group`, `get_device_credentials` and `get_devices_by_group`
    def _extracted_from_get_devices_by_group_3(self, url, arg1):
        headers = {"Authorization": f"Bearer {self.token}"}
        response = self.make_authenticated_request(url, arg1, headers=headers)
        return response.json()

    def report_consumption(self, base_url, start_date, end_date, id_groups):
        url = f"{base_url}/led/groups/consumption"
        headers = {"Authorization": f"Bearer {self.token}"}
        data = {"startDate": start_date, "endDate": end_date, "idGroups": id_groups}
        response = self.make_authenticated_request(url, "POST", json=data, headers=headers)
        return response.json()
