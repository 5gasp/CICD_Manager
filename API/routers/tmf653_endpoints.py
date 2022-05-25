# -*- coding: utf-8 -*-
# @Author: Rafael Direito
# @Date:   22-05-2022 10:25:05
# @Email:  rdireito@av.it.pt
# @Last Modified by:   Rafael Direito
# @Last Modified time: 25-05-2022 10:07:13
# @Description: 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Author: Daniel Gomes (dagomes@av.it.pt)
# Date: 1st july 2021
# Last Update: 12th july 2021

# Description:
# Constains all the endpoints related to the CI/CD Agents

# generic imports
from wsgiref import headers
from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session
from sql_app.database import SessionLocal
from sqlalchemy.orm import Session
from sql_app import crud
import sql_app.CRUD.agents as CRUD_Agents
from sql_app.schemas import TMF653 as tmf653_schemas
import logging
import inspect
import sys
import os
import aux.constants as Constants
import aux.utils as Utils
from fastapi.responses import FileResponse
import yaml
import json
import re
import binascii
import pydantic
from testing_descriptors_validator.test_descriptor_validator import Test_Descriptor_Validator
from fastapi import File, UploadFile

from wrappers.jenkins.wrapper import Jenkins_Wrapper
import routers.tests as TestRouters

# import from parent directory
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

# custom imports
import aux.utils as Utils
router = APIRouter()

# Logger
logging.basicConfig(
    format="%(module)-20s:%(levelname)-15s| %(message)s",
    level=logging.INFO
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/tmf-api/testDescriptorValidation",
    tags=["TMF-653"],
    summary="Validates a Test Descriptor",
    description="Given a TMF-653 Payload, the respective Test Descriptor will be rendered and validated",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {**Utils.response_dict,
                    "message": "The test Descriptor has been validated",
                }
            }
        }
        }
        ,
        400: {
            "content": {
                "application/json": {
                    "example": {**Utils.response_dict,
                    "message": "",
                    "success": False,
                    "errors": [
                    "Unable to parse the submitted file. Must be a YAML",
                    "Invalid Testing Descriptor format",
                    ]}
                }
            }
        }
}
)
async def validate_test_descriptor(test_descriptor:UploadFile = File(...) , db: Session = Depends(get_db) ):
    results = []

    contents = await test_descriptor.read()
    contents = contents.decode('utf-8')    
    contents = re.sub(r"(\{\{[^}]+}\})","test",contents)    
    try:
        test_descriptor_data = yaml.safe_load(contents)
    except Exception as e:
        print(e)
        return Utils.create_response(status_code=400, success=False, errors=["Unable to parse the submitted file. It must be a YAML."])

    test_descriptor_validator =  Test_Descriptor_Validator(test_descriptor_data)
    structural_validation_errors = test_descriptor_validator.validate_structure()
    if len(structural_validation_errors) != 0:
        return Utils.create_response(status_code=400, success=False, errors=structural_validation_errors)

   
    return Utils.create_response(success=True, message=f"The test Descriptor has been validated")
    

@router.post(
    "/tmf-api/serviceTestManagement/v4/serviceTest",
    tags=["TMF-653"],
    summary="Creates a Service Test",
    description="Creates a Service Test, given a Valid TMF-653 Payload file, and execute the associated tests",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {**Utils.response_dict,
                    "message": "A new build job was created",
                     "data": {
                            "test_id": 1,
                            "testbed_id" : "testbed_itav",
                            "netapp_id": "OBU",
                            "network_service_id": "vOBU",
                            "job_name": "testjob", 
                            "build_number": 1,
                            "access_token": "12345abcde"}
                }
            }
        }}
        ,
        400: {
            "content": {
                "application/json": {
                    "example": {**Utils.response_dict,
                    "message": "",
                    "success": False,
                    "errors": ["Payload does not follow TMF653 Standard",
                    "Unable to parse the submitted file",
                    "Invalid Testing Descriptor format",
                    "The selected testbed doesn't exist.",
                    "Error on validating test parameters",
                    "No CI/CD Agent Available",
                    "Couldn't create pipeline script"
                    ]}
                }
            }
        }
    }
)
async def create_service_test(serviceTestParsed: tmf653_schemas.ServiceTest_Create , db: Session = Depends(get_db)):


    # Get Service Test Characteristics
    characteristics = []
    nods_id = None
    for characteristic in serviceTestParsed.characteristic:
        # NODS_ID to later on patch data on NODS
        if characteristic.name == "NODS_ServiceTest_ID":
            nods_id=characteristic.value['value']
        characteristics.append({
            'id': characteristic.id, 
            'name': characteristic.name, 
            'valueType': characteristic.valueType,
            'value': characteristic.value
        })
    #2  ->Get the Service Test Specification Id
    service_test_specification_id = serviceTestParsed.testSpecification.id
    service_test_specification_href = serviceTestParsed.testSpecification.href
    
    #2.2 - Authenticate with the NODS
    success, token =  Utils.get_nods_token()
    #2.3 -> Query the Service Test Specification Endpoint
    try:
        success, response = Utils.get_serviceTestSpecification(token=token,_id=service_test_specification_id)
        if not success:
            return Utils.create_response(status_code=400, success=False, message=f"{response}", data=[])
    except Exception as e:
        return Utils.create_response(status_code=400, success=False, message=f"{e}", data=[])

    logging.info("Retrieved Service Test Specification")
    #3 ->  Get the attachment (testing descriptor)
   
    try:
        attachment_url = response['attachment'][0]["url"]
        success, response = Utils.get_serviceTestDescriptor(token=token,url=attachment_url)
        descriptors_text = response.text
        if not success:
            return Utils.create_response(status_code=400, success=False, message=f"{response}", data=[])
    except Exception as e:
        return Utils.create_response(status_code=400, success=False, message=f"{e}", data=[])
         
    logging.info(f"Retrieved the Testing Descriptor  from {attachment_url}")
    
    #4 -> Render Descriptor
    for characteristic in characteristics:
        descriptors_text = descriptors_text.replace(f"{{{{{characteristic['name']}}}}}", f"{characteristic['value']['value']}")
    try:
        rendered_descriptor = yaml.safe_load(descriptors_text)
    except Exception as e:
        return Utils.create_response(status_code=400, success=False, message=f"Invalid Testing Descriptor format", data=[])
    logging.info(f"Renderered the descriptor")

    return TestRouters.new_test(rendered_descriptor, db)