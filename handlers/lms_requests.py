import os
import requests
from dotenv import load_dotenv
from hashlib import md5
import json

load_dotenv()
conf = json.load(open('.env'))
class DeviceData:
    def __init__(self, pole=None, latitude=None, longitude=None, serialNumber=None, idGateway=None, idType=1):
        self.pole = pole
        self.latitude = latitude
        self.longitude = longitude
        self.serialNumber = serialNumber
        self.idGateway = idGateway
        self.idType = idType
        
    def to_json(self):
        return {
            "pole": self.pole,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "serialNumber": self.serialNumber,
            "idGateway": self.idGateway,
            "idType": self.idType
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

    def set_serialNumber(self, serialNumber):
        self.serialNumber = serialNumber

    def get_serialNumber(self):
        return self.serialNumber

    def set_idGateway(self, idGateway):
        self.idGateway = idGateway

    def get_idGateway(self):
        return self.idGateway

    def set_idType(self, idType):
        self.idType = idType

    def get_idType(self):
        return self.idType


    

class LMSRequest:
    def __init__(self, base_url):
        self.BASE_URL = base_url
        self.token = self.get_access_token()

        # self.all_groups = self.get_all_groups()
        # self.all_devices = self.get_all_devices()
        # self.all_types = self.get_all_types()
        # self.all_gateways = self.get_all_gateways()
        # self.all_commands = self.get_all_commands()
        # self.all_light_profiles = self.get_all_light_profiles()

    # Define other methods here...
    def get_access_token(self):
        url = f"{self.BASE_URL}/token"
        username = conf['LMS']['API_USERNAME']
        password = conf['LMS']["API_PASSWORD"]
        hashed_password = md5(password.encode()).hexdigest()
        data = f'grant_type=password&username={username}&password={hashed_password}&client_id=ngAuthApp'
        response = requests.post(url=url, data=data)
        response.raise_for_status()
        return response.json()['access_token']
    
    def make_authenticated_request(self,url, method, json_data=None):
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.request(method=method,url=url, headers=headers, json=json_data)
        response.raise_for_status()
        return response.json()
    
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
            "arg16": None
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
        allow_children: int = 0
    ):
        url = f"{self.BASE_URL}/led/groups"
        json_data = {
            "name": name,
            "parentGroupId": parent_group_id,
            "idNetworkType": id_network_type,
            "idDeviceType": id_device_type,
            "allowChildren": allow_children
        }
        return self.make_authenticated_request(url, "POST", json_data)

    def update_group(
        self,
        group_id: int,
        name: str,
        parent_group_id: int = None,
        id_network_type: int = 2,
        id_device_type: int = 1,
        allow_children: int = 0
    ):
        url = f"{self.BASE_URL}/led/groups/{group_id}"
        json_data = {
            "name": name,
            "parentGroupId": parent_group_id,
            "idNetworkType": id_network_type,
            "idDeviceType": id_device_type,
            "allowChildren": allow_children
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
        response = self.make_authenticated_request(url, "GET")
        return response

    def get_device_by_serial(self, group_id, serial_number):
        url = f"{self.BASE_URL}/led/groups/{group_id}/devices/{serial_number}"
        response = self.make_authenticated_request(url, "GET")
        return response.json()
    
    def create_device(self, group_id, device_data):
        url = f"{self.BASE_URL}/led/groups/{group_id}/devices"
        return self.make_authenticated_request(
            url=url, method="POST", json_data=device_data
        )

    def update_device(self, group_id, serial_number, device_data):
        url = f"{self.BASE_URL}/led/groups/{group_id}/devices/{serial_number}"
        response = self.make_authenticated_request(url, "PUT", json=device_data)
        return response.json()

    def delete_device(self, group_id, serial_number):
        url = f"{self.BASE_URL}/led/groups/{group_id}/devices/{serial_number}"
        response = self.make_authenticated_request(url, "DELETE")
        return "Device deleted successfully."
    
    def associate_device_to_group(self, group_id, serial_number, associate=0):
        url = f"{self.BASE_URL}/led/groups/{group_id}/devices/{serial_number}?associate={associate}"
        response = self.make_authenticated_request(url, "POST")
        return response.json()

    def get_all_types(self):
        url = f"{self.BASE_URL}/led/type"
        response = self.make_authenticated_request(url, "GET")
        return response.json()

    def get_type_by_id(self, type_id):
        url = f"{self.BASE_URL}/led/type/{type_id}"
        response = self.make_authenticated_request(url, "GET")
        return response.json()
    
    def create_gateway(self, name, ident, latitude, longitude, idNetworkType=None, macAddress=None):
        url = f"{self.BASE_URL}/led/gateways"
        data = {
            "name": name,
            "ident": ident,
            "latitude": latitude,
            "longitude": longitude,
            "idNetworkType": idNetworkType,
            "macAddress": macAddress
        }
        response = self.make_authenticated_request(url, "POST", json=data)
        return response.json()
    
    def get_all_gateways(self):
        url = f"{self.BASE_URL}/led/gateways"
        response = self.make_authenticated_request(url, "GET")
        return response.json()

    def get_gateway_by_id(self, idGateway):
        url = f"{self.BASE_URL}/led/gateways/{idGateway}"
        response = self.make_authenticated_request(url, "GET")
        return response.json()
    
    def update_gateway(self, idGateway, name, ident, latitude, longitude, idNetworkType=None, macAddress=None):
        url = f"{self.BASE_URL}/led/gateways/{idGateway}"
        data = {
            "name": name,
            "ident": ident,
            "latitude": latitude,
            "longitude": longitude,
            "idNetworkType": idNetworkType,
            "macAddress": macAddress
        }
        response = self.make_authenticated_request(url, "PUT", json=data)
        return response.json()

    def get_all_commands(self):
        url = f"{self.BASE_URL}/led/commands"
        response = self.make_authenticated_request(url, "GET")
        return response.json()

    def get_command_by_id(self, idCommand):
        url = f"{self.BASE_URL}/led/commands/{idCommand}"
        response = self.make_authenticated_request(url, "GET")
        return response.json()
    
    def send_group_command(self, group_id, opcode, arg1=None):
        url = f"{self.BASE_URL}/led/groups/{group_id}/commands/{opcode}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        data = {}
        if arg1 is not None:
            data["arg1"] = arg1
        response = self.make_authenticated_request(url, "POST", json=data)
        return response.json()
    
    def send_device_command(self, serial_number, opcode, arg1=None):
        url = f"{self.BASE_URL}/led/devices/{serial_number}/commands/{opcode}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        data = {}
        if arg1 is not None:
            data["arg1"] = arg1
        response = self.make_authenticated_request(url, "POST", json=data)
        return response.json()
    
    def send_gateway_command(self, gateway_id, opcode, arg1=None):
        url = f"{self.BASE_URL}/led/gateways/{gateway_id}/commands/{opcode}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        data = {}
        if arg1 is not None:
            data["arg1"] = arg1
        response = self.make_authenticated_request(url, "POST", json=data)
        return response.json()
    
    def create_light_profile(self, name, typeLP, events):
        url = f"{self.BASE_URL}/led/profiles"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        data = {
            "name": name,
            "typeLP": typeLP,
            "events": events
        }
        response = self.make_authenticated_request(url, "POST", json=data)
        return response.json()
    
    def get_all_light_profiles(self):
        url = f"{self.BASE_URL}/led/profiles"
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        response = self.make_authenticated_request(url, "GET")
        return response.json()

    def get_light_profile(self, idLP):
        url = f"{self.BASE_URL}/led/profiles/{idLP}"
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        response = self.make_authenticated_request(url, "GET")
        return response.json()
    
    def update_light_profile(self, idLP, name, typeLP, events):
        url = f"{self.BASE_URL}/led/profiles/{idLP}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        data = {
            "name": name,
            "typeLP": typeLP,
            "events": events
        }
        response = self.make_authenticated_request(url, "PUT", json=data)
        return response.json()
    
    def delete_light_profile(self, idLP):
        url = f"{self.BASE_URL}/led/profiles/{idLP}"
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        response = self.make_authenticated_request(url, "DELETE")
        return response.status_code
    
    def associate_light_profile_to_group(self, idLP, idGroup):
        url = f"{self.BASE_URL}/led/profiles/{idLP}/groups/{idGroup}"
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        response = self.make_authenticated_request(url, "POST", headers=headers)
        return response.json()

    def get_light_profiles_associated_to_groups(self):
        url = f"{self.BASE_URL}/led/profiles/groups"
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        response = self.make_authenticated_request(url, "GET", headers=headers)
        return response.json()
    
    def reassociate_light_profile_to_group(self, idLP, idGroup):
        url = f"{self.BASE_URL}/led/profiles/{idLP}/groups/{idGroup}"
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        response = self.make_authenticated_request(url, "PUT", headers=headers)
        return response.json()

    def delete_associated_light_profile_from_group(self, idLP, idGroup):
        url = f"{self.BASE_URL}/led/profiles/{idLP}/groups/{idGroup}"
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        response = self.make_authenticated_request(url, "DELETE", headers=headers)
        return response.json()
    
    def get_device_credentials(self, base_url):
        url = f"{base_url}/led/devices/credentials"
        headers = {'Authorization': f'Bearer {self.token}'}
        response = self.make_authenticated_request(url, "GET", headers=headers)
        return response.json()

    def get_devices_by_group(self, base_url, id_group):
        url = f"{base_url}/led/groups/{id_group}/devicelist"
        headers = {'Authorization': f'Bearer {self.token}'}
        response = self.make_authenticated_request(url, "GET", headers=headers)
        return response.json()
    
    def report_consumption(self, base_url, start_date, end_date, id_groups):
        url = f"{base_url}/led/groups/consumption"
        headers = {'Authorization': f'Bearer {self.token}'}
        data = {
            "startDate": start_date,
            "endDate": end_date,
            "idGroups": id_groups
        }
        response = self.make_authenticated_request(url, "POST", json=data, headers=headers)
        return response.json()




# Usage
# Now you can access data without making additional requests, e.g. lms_request.all_groups









