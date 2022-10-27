# -*- coding: utf-8 -*-
# @Author: Rafael Direito
# @Date:   23-05-2022 10:46:25
# @Email:  rdireito@av.it.pt
# @Last Modified by:   Rafael Direito
# @Last Modified time: 2022-10-27 16:53:14
# @Description: 
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi import File, UploadFile
import tarfile
import json
import copy
import yaml
import os
import io
import requests
import shutil
import base64
import constants as Constants
import json

app = FastAPI()

    
def add_characteristic(payload, name, value):
    payload["characteristic"].append(
        {
            "name": name,
            "value": {
                    "value": value
            }
        }
    )
    

def add_attachment(service_test_specification_content, test_id, attachment_name):
    
    attachment = {
      "uuid": "00000000-0000-0000-0000-000000000000",
      "atReferredType": None,
      "@baseType": "BaseEntity",
      "@schemaLocation": None,
      "@type": None,
      "href": None,
      "name": attachment_name,
      "id": "00000000-0000-0000-0000-000000000000",
      "attachmentType": None,
      "content": None,
      "description": None,
      "mimeType": None,
      "url": f"/serviceTestManagement/v4/serviceTestSpecification/{test_id}/attachment/00000000-0000-0000-0000-000000000000/{attachment_name}",
      "size": None,
      "validFor": None,
      "@referredType": None
    }
    
    service_test_specification_content["attachment"].append(attachment)
    
def load_yaml_and_write_to_file(file_path, payload):
    payload = payload.decode('utf-8')
    with open(file_path, "w") as file:
        file.write(payload)
        file.close()
    

@app.post("/new-test")
async def new_test(
    testing_descriptor: UploadFile = File(...),
    network_slice_template: UploadFile = File(...),
    tests: UploadFile = File(...),
    netapp_artifacts: UploadFile = File(...),
    ):

    onboarding_id = Constants.ONBOARDED_NETAPPS_COUNT
    Constants.ONBOARDED_NETAPPS_COUNT += 1
    
    artifacts_dir = f"static/onboarded_artifacts/{onboarding_id}"
    
    # Store Artifacts
    
    # Create directory for artifacts
    if os.path.exists(artifacts_dir) and os.path.isdir(artifacts_dir):
        shutil.rmtree(artifacts_dir)
    os.mkdir(artifacts_dir)
    
    
    # Copy all files to that dir
    
    # Testing Descriptor
    testing_descriptor_content = await testing_descriptor.read()
    load_yaml_and_write_to_file(
        f"{artifacts_dir}/testing-descriptor.yaml",
        testing_descriptor_content
    )
    
    # NEST
    network_slice_template_content = await network_slice_template.read()
    load_yaml_and_write_to_file(
        f"{artifacts_dir}/NEST.yaml",
        network_slice_template_content
    )

    # Developer Defined Tests
    tests_content = await tests.read()
    tests_content = io.BytesIO(tests_content)
    tar_file = tarfile.open(fileobj=tests_content)
    tar_file.extractall(artifacts_dir)
    tar_file.close()
    
    # NetApp Artifacts
    netapp_artifacts_content = await netapp_artifacts.read()
    netapp_artifacts_content = io.BytesIO(netapp_artifacts_content)
    tar_file = tarfile.open(fileobj=netapp_artifacts_content)
    tar_file.extractall(artifacts_dir)
    tar_file.close()
    
    
    # Opening request json file, which will be sent to the CI/CD Manager
    base_payload = None
    with open('static/nods_payloads/base_nods_initial_request.json') as json_file:
        base_payload = json.load(json_file)
        
    # Update the testSpecification Id
    base_payload["characteristic"][0]["value"]["value"] = str(onboarding_id)
    base_payload["testSpecification"]["id"] = str(onboarding_id)
    
    # Prepare the characteristics to be exported in the payload
    nods_network_info = None
    with open('static/aux/nods_network_info.json') as f:
        data = json.load(f)
        data_str = str(data).replace('\'', '\"')
        message_bytes = data_str.encode('utf-8')
        base64_bytes = base64.b64encode(message_bytes)
        nods_network_info = base64_bytes.decode('utf-8')

    
    testing_descriptor_data = yaml.safe_load(testing_descriptor_content)
    for testcase in testing_descriptor_data["test_phases"]["setup"]["testcases"]:
            testcase_id = "testcase" + str(testcase["testcase_id"])
            for param in testcase["parameters"]:
                # NODS Specific parameters
                if param["value"] == "<nods.network_info>":
                    param["value"] = nods_network_info
                add_characteristic(
                    base_payload,
                    testcase_id + "." + param["key"],
                    param["value"]
                ) 
                    
    # add test info
    add_characteristic(
        base_payload, 
        "netapp_id",
        "Prototype_NetApp"
    )
    add_characteristic(
        base_payload,
        "network_service_id",
        "Prototype_Network_Service"
    )
    add_characteristic(
        base_payload,
        "testbed_id",
        "testbed_itav"
    )        
            
    print("Tiggering a new validation process.")
    #print(json.dumps(base_payload, sort_keys=True, indent=4))
    try:
        response = requests.post(
            url=f"{Constants.CI_CD_MANAGER_URL}/tmf-api/serviceTestManagement/v4/serviceTest",
            json=base_payload,
            timeout=3
        )
        print("Status Code:", response.status_code)
        print("Response Text",response.text)
    except Exception as e:
        print(e)
        pass
    
    
    return True


@app.post("/auth/realms/openslice/protocol/openid-connect/token")
async def auth():
    print("Performing authentication.")
    with open('static/nods_payloads/auth_response.json') as json_file:
        return JSONResponse(content=json.load(json_file))


@app.get("/tmf-api/serviceTestManagement/v4/serviceTestSpecification/{id}")
async def service_test_specification(id):
    print("Getting service test specification.")
    
    # Get testing Descriptor 
    testing_descriptor_content = None
    with open(f'static/onboarded_artifacts/{id}/testing-descriptor.yaml') as td:
         testing_descriptor_content = yaml.safe_load(td.read())
         
    service_test_specification_content = None
    with open('static/nods_payloads/service_test_specification.json') as json_file:
        service_test_specification_content = json.load(json_file)
        
    service_test_specification_content["attachment"] = []
    
    # Add testing descriptor to attachments
    add_attachment(
        service_test_specification_content,
        id,
        "testing-descriptor.yaml"
        )
    
    # Add developer defined test to the attachments
    for testcase in testing_descriptor_content["test_phases"]["setup"]["testcases"]:
        if testcase["type"]  == "developer-defined":
            add_attachment(
                service_test_specification_content,
                id,
                f"{testcase['name']}.tar.gz"
            ) 
        
    return JSONResponse(content=service_test_specification_content)


@app.get("/tmf-api/serviceTestManagement/v4/serviceTestSpecification/{service_test_specification_id}/attachment/{attachement_uuid}/{attachment_name}")
async def service_test_specification(service_test_specification_id, attachement_uuid, attachment_name):
    
    
    
    if attachment_name == "testing-descriptor.yaml":
        print("Getting testing descriptor as an attachment.")
        # Get testing Descriptor
        testing_descriptor_content = None
        with open(f'static/onboarded_artifacts/{service_test_specification_id}/testing-descriptor.yaml') as td:
            testing_descriptor_content = yaml.safe_load(td.read())
        
        testing_descriptor_content["test_info"]["netapp_id"] = '{{netapp_id}}'
        testing_descriptor_content["test_info"]["network_service_id"] = "{{network_service_id}}"
        testing_descriptor_content["test_info"]["testbed_id"] = "{{testbed_id}}"
        
        for testcase in testing_descriptor_content["test_phases"]["setup"]["testcases"]:
            testcase_id = "testcase" + str(testcase["testcase_id"])
            for param in testcase["parameters"]:
                param["value"] = '{{' + testcase_id + "." + param["key"] + "}}"
        print(testing_descriptor_content)
        td_to_parse_path = f'static/onboarded_artifacts/{service_test_specification_id}/testing_descriptor_to_parse.yaml'
        f = open(td_to_parse_path, 'w')
        f.write(yaml.dump(testing_descriptor_content).replace("'", ""))
        f.close()
        

        return FileResponse(td_to_parse_path, media_type='application/octet-stream', filename="testing_descriptor_to_parse.yaml")
    
    else:
        
        filepath = td_to_parse_path = f'static/onboarded_artifacts/{service_test_specification_id}/{attachment_name}'
        return FileResponse(filepath)

        
@app.patch("/tmf-api/serviceTestManagement/v4/serviceTest/{nods_id}")
async def patchresult(nods_id, request: Request):
    print("Patching Results.")
    body = await request.json()
    print(body)
    return True
