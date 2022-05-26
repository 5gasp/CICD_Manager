# -*- coding: utf-8 -*-
# @Author: Rafael Direito
# @Date:   23-05-2022 10:46:25
# @Email:  rdireito@av.it.pt
# @Last Modified by:   Rafael Direito
# @Last Modified time: 26-05-2022 10:15:25
# @Description: 
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
import json
import copy
import yaml
import requests
from constants import CI_CD_MANAGER_URL
app = FastAPI()



TESTING_DESCRIPTOR = None
with open("static/testing_descriptor.yaml") as file:
    # The FullLoader parameter handles the conversion from YAML
    # scalar values to Python the dictionary format
    TESTING_DESCRIPTOR = yaml.load(file)

    
def add_characteristic(payload, name, value):
    payload["characteristic"].append(
        {
            "name": name,
            "value": {
                    "value": value
            }
        }
    )

@app.post("/new-test")
async def new_test():

    # Opening request json file
    base_payload = None
    with open('static/nods_payloads/base_nods_initial_request.json') as json_file:
        base_payload = json.load(json_file)
  
    # add test info
    add_characteristic(
        base_payload, 
        "netapp_id",
        TESTING_DESCRIPTOR["test_info"]["netapp_id"]
    )
    add_characteristic(
        base_payload,
        "network_service_id",
        TESTING_DESCRIPTOR["test_info"]["network_service_id"]
    )
    add_characteristic(
        base_payload,
        "testbed_id",
        TESTING_DESCRIPTOR["test_info"]["testbed_id"]
    )
    
    # add testcase characteristics
    for testcase in TESTING_DESCRIPTOR["test_phases"]["setup"]["testcases"]:
        testcase_id = "testcase" + str(testcase["testcase_id"])
        for param in testcase["parameters"]:
            add_characteristic(
                base_payload,
                testcase_id + "." + param["key"],
                param["value"]
            )
            

    print("Tiggering a new validation process.")
    try:
        response = requests.post(
            url=f"{CI_CD_MANAGER_URL}/tmf-api/serviceTestManagement/v4/serviceTest",
            json=base_payload,
            timeout=3
        )
    except Exception as e:
        pass
    #print("Status Code:", response.status_code)
    #print("Response Text",response.text)
    
    return True


@app.post("/auth/realms/openslice/protocol/openid-connect/token")
async def auth():
    print("Performing authentication.")
    with open('static/nods_payloads/auth_response.json') as json_file:
        return JSONResponse(content=json.load(json_file))


@app.get("/tmf-api/serviceTestManagement/v4/serviceTestSpecification/{id}")
async def service_test_specification(id):
    print("Getting service test specification.")
    with open('static/nods_payloads/service_test_specification.json') as json_file:
        return JSONResponse(content=json.load(json_file))


@app.get("/tmf-api/serviceTestManagement/v4/serviceTestSpecification/{service_test_specification_uuid}/attachment/{attachement_id}/{attachment_name}")
async def service_test_specification(service_test_specification_uuid, attachement_id, attachment_name):
    
    if attachment_name == "testing-descriptor.yaml":
        print("Getting testing descriptor as an attachment.")
        TESTING_DESCRIPTOR_TO_PARSE = copy.deepcopy(TESTING_DESCRIPTOR)
        
        TESTING_DESCRIPTOR_TO_PARSE["test_info"]["netapp_id"] = '{{netapp_id}}'
        TESTING_DESCRIPTOR_TO_PARSE["test_info"]["network_service_id"] = "{{network_service_id}}"
        TESTING_DESCRIPTOR_TO_PARSE["test_info"]["testbed_id"] = "{{testbed_id}}"
        
        for testcase in TESTING_DESCRIPTOR_TO_PARSE["test_phases"]["setup"]["testcases"]:
            testcase_id = "testcase" + str(testcase["testcase_id"])
            for param in testcase["parameters"]:
                param["value"] = '{{' + testcase_id + "." + param["key"] + "}}"
                
        f = open('static/testing_descriptor_to_parse.yaml', 'w')
        f.write(yaml.dump(TESTING_DESCRIPTOR_TO_PARSE).replace("'", ""))
        f.close()

        return FileResponse('static/testing_descriptor_to_parse.yaml', media_type='application/octet-stream', filename="testing_descriptor_to_parse.yaml")
    
    if attachment_name == "bandwidth.tar.gz":
        return FileResponse('static/bandwidth.tar.gz')

        
@app.patch("/tmf-api/serviceTestManagement/v4/serviceTest/{nods_id}")
async def patchresult(nods_id, request: Request):
    print("Patching Results.")
    body = await request.json()
    print(body)
    return True
