import requests
import re
import base64

NODS_HOST = "http://10.255.28.114"
NODS_USERNAME = "admin"
NODS_PASSWORD = "admin"

SERVICE_ORDER_UUID = "ca9fad40-ad7d-474c-a512-627f384f9b45"

AUTH_TOKEN = None

def get_nods_auth_token():
    global AUTH_TOKEN
    url = f"{NODS_HOST}/auth/realms/openslice/protocol/openid-connect/token"

    payload = f'client_id=osapiWebClientId&client_secret=secret&grant_type=password&username={NODS_USERNAME}&password={NODS_PASSWORD}'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.post(
        url=url,
        headers=headers,
        data=payload
    )

    response.raise_for_status()

    AUTH_TOKEN = response.json().get("access_token")
    print("NODS Auth Token:", AUTH_TOKEN)


def get_testing_agent_rfs(service_order_uuid):

    url = f"{NODS_HOST}/tmf-api/serviceOrdering/v4/serviceOrder/{service_order_uuid}"

    headers = {
    'Authorization': f"Bearer {AUTH_TOKEN}",
    }

    response = requests.get(
        url=url,
        headers=headers,
    )
    
    response.raise_for_status()

    svc_order_data = response.json()

    if svc_order_data["state"] == "COMPLETED":
        for supporting_svc in svc_order_data["orderItem"][0]["service"]["supportingService"]:
            svc_data = get_service_data(supporting_svc["id"])
            if svc_data["@type"] == "ResourceFacingService":
                process_testing_agent_data(svc_data)
    else:
        print("Service Order is not completed. Current state:", svc_order_data["state"])


def get_service_data(service_id):
    url = f"{NODS_HOST}/tmf-api/serviceInventory/v4/service/{service_id}"

    headers = {
    'Authorization': f"Bearer {AUTH_TOKEN}",
    }

    response = requests.get(
        url=url,
        headers=headers,
    )

    response.raise_for_status()
    return response.json()


def process_testing_agent_data(svc_data):
    username, password, node_port, ip = None, None, None, None

    for characteristic in svc_data["serviceCharacteristic"]:
        if characteristic["name"].endswith("jenkins.jenkins-admin-password"):
            password = base64.b64decode(characteristic["value"]["value"]).decode('utf-8')

        elif characteristic["name"].endswith("jenkins.jenkins-admin-user"):
            username = base64.b64decode(characteristic["value"]["value"]).decode('utf-8')

        elif characteristic["name"].endswith("jenkins.ports") :
            match = re.search(r'nodePort=(\d+)', characteristic["value"]["value"])
            if match:
                node_port = match.group(1)

        elif characteristic["name"] == "clusterMasterURL":
            match = re.search(r'https?://([\d.]+)', characteristic["value"]["value"])
            if match:
                ip = match.group(1)

        if username and password and node_port and ip:
            break

    url = f"http://{ip}:{node_port}/"
    print("Testing Agent Credentials:")
    print("Username:", username)
    print("Password:", password)
    print("URL:", url)  




get_nods_auth_token()
get_testing_agent_rfs(SERVICE_ORDER_UUID)