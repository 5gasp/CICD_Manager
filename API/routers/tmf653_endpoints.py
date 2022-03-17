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
from typing import List
import logging
import inspect
import sys
import os
import aux.constants as Constants
import aux.utils as Utils
from fastapi.responses import FileResponse
import requests
import yaml
import json
import binascii
import pydantic
from testing_descriptors_validator.test_descriptor_validator import Test_Descriptor_Validator
from fastapi import File, UploadFile
import re as re

from wrappers.jenkins.wrapper import Jenkins_Wrapper


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
    "/tmp-api/testDescriptorValidation",
    tags=["TMF-653"]
)
async def validate_test_descriptor(serviceTest:UploadFile = File(...) , db: Session = Depends(get_db) ):
    contents = await serviceTest.read()
    try:
        test_descriptor_data = json.loads(contents.decode("utf-8"))
        #print(test_descriptor_data)
        serviceTestParsed = tmf653_schemas.ServiceTest_Create(**test_descriptor_data)
    except pydantic.ValidationError as e:
        return Utils.create_response(status_code=400, success=False, errors=[f"Payload does not follow TMF653 Standard: {e}"])
    except:
        return Utils.create_response(status_code=400, success=False, errors=["Unable to parse the submitted file"])

    # Get Service Test Characteristics
    characteristics = []
    for characteristic in serviceTestParsed.characteristic:
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
        print(e)
        return Utils.create_response(status_code=400, success=False, message=f"{e}", data=[])
         
    logging.info(f"Retrieved the Testing Descriptor  from {attachment_url}")
    print(descriptors_text)
  
    #4 -> Render Descriptor
    for characteristic in characteristics:
        if (characteristic['name'] == "network_service_id" ):
            characteristic['name'] = 'network_service_id_test'
        descriptors_text = descriptors_text.replace(f"{{{{{characteristic['name']}}}}}", f"{characteristic['value']['value']}")
    rendered_descriptor = yaml.safe_load(descriptors_text)
    logging.info(f"Renderered the descriptor")

    
    # 5 - validate the structure of the testing descriptor
    test_descriptor_validator =  Test_Descriptor_Validator(rendered_descriptor)
    structural_validation_errors = test_descriptor_validator.validate_structure()
    if len(structural_validation_errors) != 0:
        return Utils.create_response(status_code=400, success=False, errors=structural_validation_errors)

    # # 6 - check if the testbed exists
    testbed_id = rendered_descriptor["test_info"]["testbed_id"]
    print(testbed_id)
    if crud.get_testbed_by_id(db, testbed_id) is None:
        return Utils.create_response(status_code=400, success=False, errors=["The selected testbed doesn't exist."])

    # # 7 - validate id all tests exist in the selected testbed
    testbed_tests = crud.get_test_info_by_testbed_id(db,testbed_id)
    #testbed_tests = Constants.TEST_INFO['tests'].get(testbed_id)

    errors = test_descriptor_validator.validate_tests_parameters(testbed_tests)
    if len(errors) != 0:
        return Utils.create_response(status_code=400, success=False, errors=errors, message="Error on validating test parameters")


    # # # 8 - validate metrics collection information
    # metrics_collection_information = Constants.METRICS_COLLECTION_INFO
    # is_ok = test_descriptor_validator.validate_metrics_collection_process(metrics_collection_information)
    # if not is_ok:
    #     return Utils.create_response(status_code=400, success=False, errors=errors, message="Badly defined parameters for the metrics collection process")
   
    return Utils.create_response(success=True, message=f"The test Descriptor has been validated")
    

@router.post(
    "/tmf-api/serviceTestManagement/v4/serviceTest",
    tags=["TMF-653"] 
)
async def create_service_test(serviceTest:UploadFile = File(...) , db: Session = Depends(get_db)):

    # 1 -> Get data and Validate TMF653 Payload

    contents = await serviceTest.read()
    try:
        test_descriptor_data = json.loads(contents.decode("utf-8"))
        #print(test_descriptor_data)
        serviceTestParsed = tmf653_schemas.ServiceTest_Create(**test_descriptor_data)
    except pydantic.ValidationError as e:
        return Utils.create_response(status_code=400, success=False, errors=[f"Payload does not follow TMF653 Standard: {e}"])
    except:
        return Utils.create_response(status_code=400, success=False, errors=["Unable to parse the submitted file"])

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
        print(e)
        return Utils.create_response(status_code=400, success=False, message=f"{e}", data=[])
         
    logging.info(f"Retrieved the Testing Descriptor  from {attachment_url}")
    
    #4 -> Render Descriptor
    for characteristic in characteristics:
        descriptors_text = descriptors_text.replace(f"{{{{{characteristic['name']}}}}}", f"{characteristic['value']['value']}")
    rendered_descriptor = yaml.safe_load(descriptors_text)
    logging.info(f"Renderered the descriptor")

    
    # 5 - validate the structure of the testing descriptor
    test_descriptor_validator =  Test_Descriptor_Validator(rendered_descriptor)
    structural_validation_errors = test_descriptor_validator.validate_structure()
    if len(structural_validation_errors) != 0:
        return Utils.create_response(status_code=400, success=False, errors=structural_validation_errors)

    
    # # 6 - check if the testbed exists
    testbed_id = rendered_descriptor["test_info"]["testbed_id"]
    print(testbed_id)
    if crud.get_testbed_by_id(db, testbed_id) is None:
        return Utils.create_response(status_code=400, success=False, errors=["The selected testbed doesn't exist."])


    # # 7 - validate id all tests exist in the selected testbed
    testbed_tests = crud.get_test_info_by_testbed_id(db,testbed_id)

    errors = test_descriptor_validator.validate_tests_parameters(testbed_tests)
    if len(errors) != 0:
        return Utils.create_response(status_code=400, success=False, errors=errors, message="Error on validating test parameters")


    # # 8 - validate metrics collection information
    metrics_collection_information = Constants.METRICS_COLLECTION_INFO
    is_ok = test_descriptor_validator.validate_metrics_collection_process(metrics_collection_information)
    if not is_ok:
        return Utils.create_response(status_code=400, success=False, errors=errors, message="Badly defined parameters for the metrics collection process")
   
    descriptor_metrics_collection = None
    if "metrics_collection" in rendered_descriptor["test_phases"]["setup"]:
        descriptor_metrics_collection = rendered_descriptor["test_phases"]["setup"]["metrics_collection"]



    #  # 9 - register the test in database
    netapp_id = rendered_descriptor["test_info"]["netapp_id"]
    network_service_id = rendered_descriptor["test_info"]["network_service_id"]

    # # 10.a register new test
    test_instance = crud.create_test_instance(db, netapp_id, network_service_id, testbed_id,nods_id=nods_id)

    # # 10.b update test status
    crud.create_test_status(db, test_instance.id, Constants.TEST_STATUS["submitted_on_manager"], True)


    # # Check if the CI/CD Node for this test is already registered
    
    testbeds_ci_cd_agents = CRUD_Agents.get_ci_cd_agents_by_testbed(db, testbed_id)
    available_agents_jobs = []
    for ci_cd_agent in testbeds_ci_cd_agents:
        jenkins_wrapper = Jenkins_Wrapper()
        ret, message = jenkins_wrapper.connect_to_server(ci_cd_agent.url, ci_cd_agent.username, ci_cd_agent.password)
        if ret:
            active_jobs = [job['color'] for job in jenkins_wrapper.get_jobs()[1]].count('blue_anime')
            available_agents_jobs.append((jenkins_wrapper, ci_cd_agent, active_jobs))
    
    if len(available_agents_jobs) == 0:
         return Utils.create_response(status_code=400, success=False, errors=["No CI/CD Agent Available"])

    selected_ci_cd_agent_info = sorted(available_agents_jobs, key=lambda e: e[2])[0]
    jenkins_wrapper = selected_ci_cd_agent_info[0]
    selected_ci_cd_node = selected_ci_cd_agent_info[1]
    
    crud.update_test_instance_ci_cd_agent(db, test_instance.id , selected_ci_cd_node.id)
    crud.create_test_status(db, test_instance.id, Constants.TEST_STATUS["ci_cd_agent_auth"], True)

    # # create jenkins  credentials
    # # a - communication token
    credential_id = "communication_token"
    credential_secret = binascii.b2a_hex(os.urandom(16)).decode('ascii')
    credential_description = "Token used for communication with the CI/CD Manager" 
    ret, message = jenkins_wrapper.create_credential(credential_id, credential_secret, credential_description)
    if not ret:
        crud.create_test_status(db, test_instance.id, Constants.TEST_STATUS["created_comm_token"], False)
        return Utils.create_response(status_code=400, success=False, errors=[message])
    crud.create_test_status(db, test_instance.id, Constants.TEST_STATUS["created_comm_token"], True)
    
    testbed_id = test_instance.testbed_id
    ltr_info = Utils.get_ltr_info_for_testbed(testbed_id)

    # # b - ftp_user
    ret, message = jenkins_wrapper.create_credential("ltr_user", ltr_info["user"], "FTP user for obtaining the tests.")
    if not ret:
        return Utils.create_response(status_code=400, success=False, errors=[message])
    # c - ftp_password
    ret, message = jenkins_wrapper.create_credential("ltr_password", ltr_info["password"], "FTP password for obtaining the tests.")
    if not ret:
        return Utils.create_response(status_code=400, success=False, errors=[message])

    # # update communication credential on db
    logging.info(f"credential_secret: {credential_secret}")
    selected_ci_cd_node = CRUD_Agents.update_communication_token(db, selected_ci_cd_node.id, credential_secret)
    
    executed_tests_info = test_descriptor_validator.executed_tests_info

    # # create jenkins pipeline script
    try:
        pipeline_config = jenkins_wrapper.create_jenkins_pipeline_script(executed_tests_info, testbed_tests, descriptor_metrics_collection, metrics_collection_information, test_instance.id, test_instance.testbed_id)
        crud.create_test_status(db, test_instance.id, Constants.TEST_STATUS["created_pipeline_script"], True)
    except Exception as e:
        crud.create_test_status(db, test_instance.id, Constants.TEST_STATUS["created_pipeline_script"], False)
        return Utils.create_response(status_code=400, success=False, errors=["Couldn't create pipeline script: " + str(e)])

    # # submit pipeline scripts
    job_name = netapp_id + '-' + network_service_id + '-' + str(test_instance.build)
    print(job_name)
    ret, message = jenkins_wrapper.create_new_job(job_name, pipeline_config)
    if not ret:
        crud.create_test_status(db, test_instance.id, Constants.TEST_STATUS["submitted_pipeline_script"], False)
        return Utils.create_response(status_code=400, success=False, errors=[message])
    crud.create_test_status(db, test_instance.id, Constants.TEST_STATUS["submitted_pipeline_script"], True)
    jenkins_job_name = message

    for executed_test in executed_tests_info:
        test_instance_test = crud.create_test_instance_test(db, test_instance.id, f"{executed_test['name']}-test-id-{executed_test['testcase_id']}", executed_test["description"])
        logging.info(f"Registered test '{test_instance_test.performed_test}' for test instance {test_instance.id}.")

    # # run jenkins job
    ret, message = jenkins_wrapper.run_job(jenkins_job_name)
    if not ret:
        return Utils.create_response(status_code=400, success=False, errors=[message])
    build_id = message

    # # get jenkins job build number
    ret, message = jenkins_wrapper.get_last_build_number(job_name)
    if not ret:
        return Utils.create_response(status_code=400, success=False, errors=[message])
    job_build_number = message

    # # Update extra information
    crud.update_test_instance_extra_info(db, test_instance.id, str({"job_name": job_name, "build_number": job_build_number}))

    return Utils.create_response(success=True, message=f"A new build job was created", data={
        "test_id": test_instance.id,
        "testbed_id" : test_instance.testbed_id,
        "netapp_id": netapp_id,
        "network_service_id": network_service_id,
        "job_name": jenkins_job_name, 
        "build_number": job_build_number,
        "access_token": test_instance.access_token
        })
