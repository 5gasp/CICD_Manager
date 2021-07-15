#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Author: Rafael Direito (rdireito@av.it.pt)
# Date: 1st july 2021
# Last Update: 12th july 2021

# Description:
# Constains all the endpoints related to the testing of the NetApps

# generic imports
from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session
from sql_app.database import SessionLocal
from sql_app import crud, schemas
from fastapi import File, UploadFile
from sqlalchemy.orm import Session
import logging
import inspect
import sys
import os
import binascii
import yaml

# import from parent directory
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

# custom imports
from wrappers.jenkins_wrapper import Jenkins_Wrapper
from aux.test_descriptor_validator import Test_Descriptor_Validator
import aux.constants as Constants
import utils.utils as Utils

# Logger
logging.basicConfig(
    format="%(module)-15s:%(levelname)-10s| %(message)s",
    level=logging.INFO
)

router = APIRouter()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/tests/all", tags=["tests"])
async def all_tests(db: Session = Depends(get_db)):
    data = Constants.TEST_INFO
    return Utils.create_response(data=data)


@router.get("/tests/per-testbed", tags=["tests"])
async def tests_per_testbed(testbed: str):
    testbed_tests = Constants.TEST_INFO['tests'].get(testbed, None)
    if testbed_tests:
        data = {"tests": testbed_tests}
        return Utils.create_response(data=data)
    else:
        return Utils.create_response(status_code=400, success=False, errors=["The testbed you chose doesn't exist."])

@router.get("/tests/test-status", tags=["tests"])
async def get_test_status(netapp_id: str, network_service_id: str , db: Session = Depends(get_db)):
    try:
        data = crud.get_all_test_status_for_test(db, netapp_id, network_service_id)
        return Utils.create_response(data=data)
    except Exception as e:
        logging.error(e)
        return Utils.create_response(status_code=400, success=False, errors=["Couldn't retrieve the tests status for the netapp and network_service you chose."]) 


@router.post("/tests/test-status", tags=["tests"])
async def update_test_status(test_status: schemas.Test_Status_Update,  db: Session = Depends(get_db)):
    try:
        crud.create_test_status_ci_cd_agent(db, test_status)
        return Utils.create_response()
    except Exception as e:
        return Utils.create_response(status_code=400, success=False, errors=["Couldn't update test status."]) 


@router.post("/tests/new")
async def new_test(test_descriptor: UploadFile = File(...),  db: Session = Depends(get_db)):

    # 1 - get data from the uploaded descriptor
    contents = await test_descriptor.read()
    try:
        test_descriptor_data = yaml.safe_load(contents.decode("utf-8"))
    except:
        return Utils.create_response(status_code=400, success=False, errors=["Unable to parse the submitted file. It must be a YAML."])

    # 2 - validate the base test info
    ok, errors = Test_Descriptor_Validator.base_validation(test_descriptor_data)
    if not ok:
        return Utils.create_response(status_code=400, success=False, errors=errors)

    # 3 - check if the testbed exists
    testbed_id = test_descriptor_data["test_info"]["testbed_id"]
    if crud.get_testbed_by_id(db, testbed_id) is None:
        return Utils.create_response(status_code=400, success=False, errors=["The selected testbed doesn't exist."])


    # 4 - validate id all tests exist in the selected testbed
    testbed_tests = Constants.TEST_INFO['tests'].get(testbed_id)
    errors = []
    for test_name, test_info in test_descriptor_data["tests"].items():
        ok, error_message = Test_Descriptor_Validator.is_test_description_valid(test_name, test_info, testbed_tests)
        if not ok:
            errors.append(error_message)
    if len(errors) != 0:
        return Utils.create_response(status_code=400, success=False, errors=errors)

    # 5 - register the test in database
    netapp_id = test_descriptor_data["test_info"]["netapp_id"]
    network_service_id = test_descriptor_data["test_info"]["network_service_id"]

    # 5.a register new test
    test_instance = crud.create_test_instance(db, netapp_id, network_service_id, testbed_id)

    # 5.b update test status
    crud.create_test_status(db, test_instance.id, Constants.TEST_STATUS["submitted_on_manager"], True)


    # Check if the CI/CD Node for this test is already registered
    selected_ci_cd_node = crud.get_ci_cd_node_by_netapp_and_network_service(db, netapp_id, network_service_id)
    if selected_ci_cd_node is None or not selected_ci_cd_node.is_online:
        crud.create_test_status(db, test_instance.id, Constants.TEST_STATUS["ci_cd_agent_provisioned"], False)
        return Utils.create_response(status_code=400, success=False, errors=[f"It doesn't exist a CI/CD node for the netapp_id {netapp_id}, network_service_id {network_service_id}, or it is offline."])
    crud.update_ci_cd_agent(db, test_instance.id, selected_ci_cd_node.id)
    crud.create_test_status(db, test_instance.id, Constants.TEST_STATUS["ci_cd_agent_provisioned"], True)

    # create jenkins connection
    jenkins_wrapper = Jenkins_Wrapper()

    # connect to jenkins server
    ret, message = jenkins_wrapper.connect_to_server(f"http://{selected_ci_cd_node.ip}:8080/", selected_ci_cd_node.username, selected_ci_cd_node.password)
    if not ret:
        crud.create_test_status(db, test_instance.id, Constants.TEST_STATUS["ci_cd_agent_auth"], False)
        return Utils.create_response(status_code=400, success=False, errors=[message])
    crud.create_test_status(db, test_instance.id, Constants.TEST_STATUS["ci_cd_agent_auth"], True)

    # create jenkins  credentials
    # a - communication token
    credential_id = "communication_token"
    credential_secret = binascii.b2a_hex(os.urandom(16)).decode('ascii')
    credential_description = "Token used for communication with the CI/CD Manager" 
    ret, message = jenkins_wrapper.create_credential(credential_id, credential_secret, credential_description)
    if not ret:
        crud.create_test_status(db, test_instance.id, Constants.TEST_STATUS["created_comm_token"], False)
        return Utils.create_response(status_code=400, success=False, errors=[message])
    crud.create_test_status(db, test_instance.id, Constants.TEST_STATUS["created_comm_token"], True)
    
    # b - ftp_user
    ret, message = jenkins_wrapper.create_credential("ftp_user", Constants.FTP_USER, "FTP user for obtaining the tests.")
    if not ret:
        return Utils.create_response(status_code=400, success=False, errors=[message])
    # c - ftp_password
    ret, message = jenkins_wrapper.create_credential("ftp_password", Constants.FTP_PASSWORD, "FTP password for obtaining the tests.")
    if not ret:
        return Utils.create_response(status_code=400, success=False, errors=[message])

    # update communication credential on db
    logging.info(f"credential_secret: {credential_secret}")
    selected_ci_cd_node = crud.update_communication_token(db, selected_ci_cd_node.id, credential_secret)
    
    # create jenkins pipeline script
    try:
        pipeline_config = jenkins_wrapper.create_jenkins_pipeline_script(test_descriptor_data["tests"], testbed_tests, test_instance.id)
        crud.create_test_status(db, test_instance.id, Constants.TEST_STATUS["created_pipeline_script"], True)
    except Exception as e:
        crud.create_test_status(db, test_instance.id, Constants.TEST_STATUS["created_pipeline_script"], False)
        return Utils.create_response(status_code=400, success=False, errors=["Couldn't create pipeline script: " + str(e)])
    
    # submit pipeline scripts
    job_name = netapp_id + '-' + network_service_id + '-' + str(test_instance.build)
    ret, message = jenkins_wrapper.create_new_job(job_name, pipeline_config)
    if not ret:
        crud.create_test_status(db, test_instance.id, Constants.TEST_STATUS["submitted_pipeline_script"], False)
        return Utils.create_response(status_code=400, success=False, errors=[message])
    crud.create_test_status(db, test_instance.id, Constants.TEST_STATUS["submitted_pipeline_script"], True)
    jenkins_job_name = message

    # run jenkins job
    ret, message = jenkins_wrapper.run_job(jenkins_job_name)
    if not ret:
        return Utils.create_response(status_code=400, success=False, errors=[message])
    build_id = message

    return Utils.create_response(success=True, message=f"A new build job was created", data={"job_name": jenkins_job_name, "build_id": build_id})