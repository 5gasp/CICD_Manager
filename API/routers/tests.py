# -*- coding: utf-8 -*-
# @Author: Rafael Direito
# @Date:   24-05-2022 10:49:25
# @Email:  rdireito@av.it.pt
# @Last Modified by:   Rafael Direito
# @Last Modified time: 09-06-2022 16:46:42
# @Description: Constains all the endpoints related to the testing of the NetApps


# generic imports
from distutils.log import error
from fastapi import APIRouter
from fastapi import Depends
from pydantic import NoneIsAllowedError
from fastapi.responses import JSONResponse, StreamingResponse, Response
from sqlalchemy.orm import Session
from sql_app.database import SessionLocal
from sql_app import crud
import sql_app.CRUD.agents as CRUD_Agents
from sql_app.schemas import ci_cd_manager as ci_cd_manager_schemas, test_info as testinfo_schemas
import test_helpers.developer_defined as dev_defined_test_helpers
from fastapi import File, UploadFile
from sqlalchemy.orm import Session
import logging
import inspect
import sys
import os
import binascii
import yaml
import datetime as dt
from urllib.request import urlopen
import xml.etree.ElementTree as ET
import json
import ftplib
import io

# import from parent directory
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

# custom imports
from wrappers.jenkins.wrapper import Jenkins_Wrapper
from testing_descriptors_validator.test_descriptor_validator import Test_Descriptor_Validator
import aux.constants as Constants
import aux.utils as Utils

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


@router.get(
    "/tests/all",
    tags=["tests"],
    summary="Get all tests",
    description="This endpoint provides a list of all the tests that exist in the database.",
)
async def all_tests(db: Session = Depends(get_db)):
    data = Constants.TEST_INFO
    return Utils.create_response(data=data)


@router.get(
    "/tests/per-testbed",
    tags=["tests"],
    summary="Get testbed's tests",
    description="The developers may use this endpoint to get a listing of all the standard tests provided by a testbed.",
)
async def tests_per_testbed(testbed: str):
    testbed_tests = Constants.TEST_INFO['tests'].get(testbed, None)
    if testbed_tests:
        data = {"tests": testbed_tests}
        return Utils.create_response(data=data)
    else:
        return Utils.create_response(status_code=400, success=False, errors=["The testbed you chose doesn't exist."])


@router.get(
    "/tests/test-status",
    tags=["tests"],
    summary="Get the status of test",
    description="The developers/apis/web_ui uses this endpoint to gather the status of a test",
)
async def get_test_status(netapp_id: str, network_service_id: str , db: Session = Depends(get_db)):
    try:
        data = crud.get_all_test_status_for_test(db, netapp_id, network_service_id)
        return Utils.create_response(data=data)
    except Exception as e:
        logging.error(e)
        return Utils.create_response(status_code=400, success=False, errors=["Couldn't retrieve the tests status for the netapp and network_service you chose."]) 


@router.post(
    "/tests/test-status",
    tags=["tests"],
    summary="Update the status of a test",
    description="When the CI Agent is performing the tests, it will use this endpoint to update their status.",
)
async def update_test_status(test_status: ci_cd_manager_schemas.Test_Status_Update,  db: Session = Depends(get_db)):
    try:
        crud.create_test_status_ci_cd_agent(db, test_status)            
        return Utils.create_response()
    except Exception as e:
        return Utils.create_response(status_code=400, success=False, errors=[f"Couldn't update test status - {e}."]) 


@router.post(
    "/tests/test-information",
    tags=["tests"],
    summary="Store Tests Information on DB",
    description="Store the information of Tests available on the CI/CD Manager",
)
async def store_test_information(test_info: testinfo_schemas.TestInformation, db: Session = Depends(get_db)):
    #TODO: Validate more fields?
    instance,msg = crud.create_test_information(db,testinfo_data=test_info)
    if instance:
        return Utils.create_response(data=instance.as_dict())
    else:
        return Utils.create_response(status_code=400,
         errors=[msg])



@router.post(
    "/tests/new", 
    tags=["tests"],
    summary="Create a new test",
    description="Given a file with a test descriptor, create a new test.",
)
async def new_test(test_descriptor: UploadFile = File(...),  db: Session = Depends(get_db)):
    # Get data from the uploaded descriptor
    contents = await test_descriptor.read()
    try:
        test_descriptor_data = yaml.safe_load(contents.decode("utf-8"))
    except:
        return Utils.create_response(status_code=400, success=False, errors=["Unable to parse the submitted file. It must be a YAML."])

    return new_test(test_descriptor_data, None, None, db)
    
    
def new_test(test_descriptor_data, nods_id, developer_defined_tests, db):
    #  validate the structure of the testing descriptor
    test_descriptor_validator = Test_Descriptor_Validator(test_descriptor_data)
    structural_validation_errors = test_descriptor_validator.validate_structure()
    if len(structural_validation_errors) != 0:
        return Utils.create_response(status_code=400, success=False, errors=structural_validation_errors)

    # check if the testbed exists
    testbed_id = test_descriptor_data["test_info"]["testbed_id"]
    if crud.get_testbed_by_id(db, testbed_id) is None:
        logging.error("The selected testbed doesn't exist.")
        return Utils.create_response(status_code=400, success=False, errors=["The selected testbed doesn't exist."])

    # validate id all tests exist in the selected testbed
    testbed_tests = crud.get_test_info_by_testbed_id(db, testbed_id)


    errors = test_descriptor_validator.validate_tests_parameters(testbed_tests)
    if len(errors) != 0:
        logging.error(f"Error on validating test parameters - {errors}")
        return Utils.create_response(status_code=400, success=False, errors=errors, message="Error on validating test parameters")

    # validate metrics collection information
    metrics_collection_information = Constants.METRICS_COLLECTION_INFO
    is_ok = test_descriptor_validator.validate_metrics_collection_process(
        metrics_collection_information)
    if not is_ok:
        logging.error(f"Error on validating metrics collection process - {errors}")
        return Utils.create_response(status_code=400, success=False, errors=errors, message="Badly defined parameters for the metrics collection process")

    descriptor_metrics_collection = None
    if "metrics_collection" in test_descriptor_data["test_phases"]["setup"]:
        descriptor_metrics_collection = test_descriptor_data[
            "test_phases"]["setup"]["metrics_collection"]

    print("HERE")
    # register the test in database
    netapp_id = test_descriptor_data["test_info"]["netapp_id"]
    network_service_id = test_descriptor_data["test_info"]["network_service_id"]

    # register new test
    test_instance = crud.create_test_instance(
        db, netapp_id, network_service_id, testbed_id, nods_id=nods_id)
    
    print("HERE")
    # update test status
    crud.create_test_status(
        db, test_instance.id, Constants.TEST_STATUS["submitted_on_manager"], True)

    # Check if the CI/CD Node for this test is already registered
    testbeds_ci_cd_agents = CRUD_Agents.get_ci_cd_agents_by_testbed(
        db, testbed_id)
    available_agents_jobs = []
    for ci_cd_agent in testbeds_ci_cd_agents:
        jenkins_wrapper = Jenkins_Wrapper()
        ret, message = jenkins_wrapper.connect_to_server(
            ci_cd_agent.url, ci_cd_agent.username, ci_cd_agent.password)
        if ret:
            active_jobs = [job['color'] for job in jenkins_wrapper.get_jobs()[
                1]].count('blue_anime')
            available_agents_jobs.append(
                (jenkins_wrapper, ci_cd_agent, active_jobs))

    print("HERE")
    if len(available_agents_jobs) == 0:
        return Utils.create_response(status_code=400, success=False, errors=["No CI/CD Agent Available"])

    selected_ci_cd_agent_info = sorted(
        available_agents_jobs, key=lambda e: e[2])[0]
    jenkins_wrapper = selected_ci_cd_agent_info[0]
    selected_ci_cd_node = selected_ci_cd_agent_info[1]

    crud.update_test_instance_ci_cd_agent(
        db, test_instance.id, selected_ci_cd_node.id)
    crud.create_test_status(db, test_instance.id,
                            Constants.TEST_STATUS["ci_cd_agent_auth"], True)


    executed_tests_info = test_descriptor_validator.executed_tests_info

    # register tests in database and prepare them to be added to the pipeline script
    for executed_test in executed_tests_info:
        performed_test = None
        is_developer_defined = False
        developer_defined_test_filepath = None
        if executed_test["type"] == "predefined":
            # db required info
            performed_test = f"{executed_test['name']}-test-id-{executed_test['testcase_id']}"
            # add extra parameters
            executed_test["full_name"] = f"{executed_test['name']}-test-id-{executed_test['testcase_id']}"
            
        elif executed_test["type"] == "developer-defined":
            # db required info
            performed_test = f"dev-defined-{executed_test['name']}-test-id-{executed_test['testcase_id']}"
            is_developer_defined = True
            developer_defined_test_filepath = developer_defined_tests[executed_test['name']]
            # add extra parameters
            executed_test["location"] = developer_defined_tests[executed_test['name']]
            executed_test["test_instance_id"] = test_instance.id
            executed_test["full_name"] = f"dev-defined-{executed_test['name']}-test-id-{executed_test['testcase_id']}"
        
        test_instance_test = crud.create_test_instance_test(
            db=db,
            test_instance_id=test_instance.id,
            performed_test=performed_test,
            description=executed_test["description"],
            is_developer_defined=is_developer_defined,
            developer_defined_test_filepath=developer_defined_test_filepath
        )
        
        logging.info(
                f"Registered {executed_test['type']} test " \
                f"'{test_instance_test.performed_test}' for test instance "\
                f" {test_instance.id}."
            )
  
    # create jenkins pipeline script
    try:
        pipeline_config = jenkins_wrapper.create_jenkins_pipeline_script(
            executed_tests_info, 
            #developer_defined_tests_for_pipeline,
            testbed_tests, 
            descriptor_metrics_collection, 
            metrics_collection_information, 
            test_instance.id, 
            test_instance.testbed_id
        )
        crud.create_test_status(
            db, test_instance.id, Constants.TEST_STATUS["created_pipeline_script"], True)
    except Exception as e:
        logging.error("Couldn't create pipeline script: " + str(e))
        crud.create_test_status(
            db, test_instance.id, Constants.TEST_STATUS["created_pipeline_script"], False)
        return Utils.create_response(status_code=400, success=False, errors=["Couldn't create pipeline script: " + str(e)])
     
     
    # submit pipeline scripts
    job_name = netapp_id + '-' + network_service_id + \
        '-' + str(test_instance.build)
    ret, message = jenkins_wrapper.create_new_job(job_name, pipeline_config)
    if not ret:
        crud.create_test_status(
            db, test_instance.id, Constants.TEST_STATUS["submitted_pipeline_script"], False)
        return Utils.create_response(status_code=400, success=False, errors=[message])
    crud.create_test_status(
        db, test_instance.id, Constants.TEST_STATUS["submitted_pipeline_script"], True)
    jenkins_job_name = message
    
    # run jenkins job
    ret, message = jenkins_wrapper.run_job(jenkins_job_name)
    if not ret:
        return Utils.create_response(status_code=400, success=False, errors=[message])
    build_id = message

    # get jenkins job build number
    ret, message = jenkins_wrapper.get_last_build_number(job_name)
    if not ret:
        return Utils.create_response(status_code=400, success=False, errors=[message])
    job_build_number = message

    # Update extra information
    crud.update_test_instance_extra_info(db, test_instance.id, str(
        {"job_name": job_name, "build_number": job_build_number}))

    return Utils.create_response(success=True, message=f"A new build job was created", data={
        "test_id": test_instance.id,
        "testbed_id": test_instance.testbed_id,
        "netapp_id": netapp_id,
        "network_service_id": network_service_id,
        "job_name": jenkins_job_name,
        "build_number": job_build_number,
        "access_token": test_instance.access_token
    })

@router.post(
"/tests/publish-test-results",
tags=["tests"],
summary="Publish test results",
description="After the validation process this endpoint will be used to submit the results to the CI/CD Manager ",
)
async def publish_test_results(test_results_information: ci_cd_manager_schemas.Test_Results,  db: Session = Depends(get_db)):
    
    # get test results
    tests = crud.get_tests_of_test_instance(db, test_results_information.test_id)
    tests = [t.performed_test for t in tests]
    print("HERE1")
    payload = {'characteristic': []}
    counter = 1
    test_instance_dic = crud.get_test_instances_by_id(db, test_results_information.test_id)

    try:
        for test in tests:
            print("-------", test)
            ftp_url = Constants.FTP_RESULTS_URL.split(":")[0] if ":" in Constants.FTP_RESULTS_URL else Constants.FTP_RESULTS_URL
            xml_str = urlopen(
                f"ftp://{Constants.FTP_RESULTS_USER}:{Constants.FTP_RESULTS_PASSWORD}@{ftp_url}/{test_results_information.ftp_results_directory}/{test}/output.xml").read()
            root = ET.fromstring(xml_str)
            failed_tests = int(root.findall("statistics")[0].find('total').find('stat').attrib['fail'])
            
            start_timestamp = root.findall("suite")[0].findall('status')[0].attrib['starttime'].split(".")[0]
            end_timestamp = root.findall("suite")[0].findall('status')[-1].attrib['endtime'].split(".")[0]
            
            start_date, start_time = start_timestamp.split()
            start_dt = dt.datetime.strptime(start_time, '%H:%M:%S').replace(year=int(start_date[0:4]), month=int(start_date[4:6]), day=int(start_date[6:8]))
            end_date, end_time = end_timestamp.split()
            end_dt = dt.datetime.strptime(end_time, '%H:%M:%S').replace(year=int(end_date[0:4]), month=int(end_date[4:6]), day=int(end_date[6:8]))

            success = failed_tests == 0
            crud.update_test_status_of_test_instance(db, test_results_information.test_id, test, str(start_dt), str(end_dt), success)
            token = test_instance_dic['access_token']
            url = f'{Constants.TRVD_HOST}/test-information.html?test_id={test_results_information.test_id}&access_token={token}'
            payload['characteristic'].append({'name': f'testResultsURL{counter}', 'value': {'value': url}  })
            counter+=1
        print(payload)

        # get test console log

        extra_information = json.loads(test_instance_dic['extra_information'].replace("'", "\""))
        selected_ci_cd_node = crud.get_ci_cd_agent_given_test_instance_id(db, test_results_information.test_id)

        if selected_ci_cd_node is None or not selected_ci_cd_node.is_online:
            return Utils.create_response(status_code=400, success=False, errors=[f"It doesn't exist a CI/CD Agent for the selected testbed, or it is offline."])
        
        jenkins_wrapper = Jenkins_Wrapper() 
        
        ret, message = jenkins_wrapper.connect_to_server(selected_ci_cd_node.url, selected_ci_cd_node.username, selected_ci_cd_node.password)
        if not ret:
            return Utils.create_response(status_code=400, success=False, errors=[message])

        ret, message = jenkins_wrapper.get_build_log(extra_information['job_name'], extra_information['build_number'])
        if not ret:
            return Utils.create_response(status_code=400, success=False, errors=[message])
        
        testbed_id = test_instance_dic["testbed_id"]
        # save console log to ftp
        session = ftplib.FTP(Constants.FTP_RESULTS_URL.split(':')[0], Constants.FTP_RESULTS_USER, Constants.FTP_RESULTS_PASSWORD)
        session.storbinary(f'STOR {test_results_information.ftp_results_directory}/console_log.log', io.BytesIO(message.encode('utf-8')) )
        session.quit()

        # update test instance
        crud.update_test_instance_after_validation_process(db, test_results_information.test_id , f"{test_results_information.ftp_results_directory}/console_log.log", test_results_information.ftp_results_directory)

        # patch data on NODS
        _,token = Utils.get_nods_token()
        nods_id = test_instance_dic['nods_id']
        Utils.patch_results(token,nods_id,payload)
        return Utils.create_response(data=tests)
    except Exception as e:
        print(e)
        return Utils.create_response(status_code=400, success=False, errors=["Couldn't get performed test status."]) 



@router.get(
    "/tests/test-report",
    tags=["tests"],
    summary="Get the report of test process",
    description="The developers can use this endpoint to gather the report of a test",
)
async def get_test_status(test_id: int, access_token: str, db: Session = Depends(get_db)):
    # test status
    test_status = None
    try:
        data = crud.get_all_test_status_for_test_given_id(db, test_id)
        test_status = [status.as_dict() for status in data]
    except Exception as e:
        logging.error(e)
        return Utils.create_response(status_code=400, success=False, errors=["Couldn't retrieve the tests status."]) 

    # test base info
    test_base_info = None
    try:
        data = crud.get_test_base_information(db, test_id)
        test_base_info = data
    except Exception as e:
        logging.error(e)
        return Utils.create_response(status_code=400, success=False, errors=["Couldn't retrieve the test base information."]) 

    # tests performed
    tests_performed = None
    try:
        data = crud.get_tests_of_test_instance(db, test_id)
        tests_performed = [d.as_dict() for d in data]
    except Exception as e:
        logging.error(e)
        return Utils.create_response(status_code=400, success=False, errors=["Couldn't retrieve the test performed."]) 


    return Utils.create_response(data={
        "test_status": test_status,
        "test_base_info": test_base_info,
        "tests_performed": tests_performed,
    })


@router.get(
    "/tests/developer-defined",
    tags=["tests"],
    summary="",
    description="",
)
async def get_developer_defined_tests(
        test_instance_test: ci_cd_manager_schemas.Test_Results,  
        db: Session = Depends(get_db)
    ) -> JSONResponse:
    
    test_instance_id = test_instance_test.test_instance_id
    communication_token = test_instance_test.communication_token
    
    
    data = crud.get_developer_defined_tests_for_test_instance(
        db, test_instance_id, communication_token
    )
    
    return Utils.create_response(data=data)


@router.get(
    "/tests/developer-defined",
    tags=["tests"],
    summary="",
    description="",
)
async def get_developer_defined_tests(
    test_instance_test: ci_cd_manager_schemas.Test_Instance_Test_Base,
    db: Session = Depends(get_db)
) -> JSONResponse:

    test_instance_id = test_instance_test.test_instance_id
    communication_token = test_instance_test.communication_token

    data = crud.get_developer_defined_tests_for_test_instance(
        db, test_instance_id, communication_token
    )

    return Utils.create_response(data=data)


@router.get(
    "/tests/download-developer-defined",
    tags=["tests"],
    summary="",
    description="",
)
async def download_developer_defined_test(
    test_instance_test: ci_cd_manager_schemas.Test_Instance_Test_Download,
    db: Session = Depends(get_db)
    ) -> JSONResponse:

    test_instance_id = test_instance_test.test_instance_id
    communication_token = test_instance_test.communication_token
    developer_defined_test_name = test_instance_test.developer_defined_test_name

    file_location = crud.get_developer_defined_test_for_test_instance(
        db, test_instance_id, communication_token, developer_defined_test_name
    )
    test_content = dev_defined_test_helpers.download_test_from_ftp(file_location)
    
    
    return Response(test_content, media_type="application/tar+gzip")
