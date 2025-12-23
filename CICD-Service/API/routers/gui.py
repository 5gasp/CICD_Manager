#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Author: Rafael Direito (rdireito@av.it.pt)
# Date: 1st july 2021
# Last Update: 21st september 2021

# Description:
# Constains all the endpoints called by the GUi

# generic imports
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from fastapi.responses import HTMLResponse

from fastapi import Depends
from sqlalchemy.orm import Session
from sql_app.database import SessionLocal
from sql_app import crud
from sqlalchemy.orm import Session
import logging
import inspect
import sys
import os
import datetime
from urllib.request import urlopen

from sql_app.schemas import ci_cd_manager as ci_cd_manager_schemas
from sql_app.schemas import test_info as test_info_schemas

# import from parent directory
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

# custom imports
from wrappers.jenkins.wrapper import Jenkins_Wrapper
import aux.constants as Constants
import aux.utils as Utils

# Logger
logging.basicConfig(
    format="%(module)-15s:%(levelname)-10s| %(message)s",
    level=logging.INFO
)

router = APIRouter()
jenkins_wrapper = Jenkins_Wrapper()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@router.get(
    "/gui/testing-process-status",
    tags=["gui"],
    summary="Get Testing Process Status",
    description="Gets all the stages of the testing process and their status.",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {**Utils.response_dict,
                    "message": "",
                    "data": ci_cd_manager_schemas.Test_Status(
                        test_id=1,
                        state="ENVIRONMENT_SETUP_CI_CD_AGENT",
                        success=True,
                        id=1,
                        timestamp=datetime.datetime.now()
                    ).dict()}
                }
            }
        },
        403: {
            "content": {
                "application/json": {
                    "example": {**Utils.response_dict,
                    "message": "",
                    "success": False,
                    "errors": ["Invalid credentials."]
                    }
                }
            }
        },
        400: {
            "content": {
                "application/json": {
                    "example": {**Utils.response_dict,
                    "message": "",
                    "success": False,
                    "errors": ["Couldn't retrieve the tests status."]
                    }
                }
            }
        }
    }
)
async def get_testing_process_status(test_id: int, access_token: str, db: Session = Depends(get_db)):
    try:
        data = crud.get_all_test_status_for_test_given_id(db, test_id, access_token)
        data = [t.as_dict() for t in data]
        data.sort(key=lambda x: x["timestamp"])
        for status in data:
            status["state"] = status["state"].value
        if not data:
            return Utils.create_response(status_code=403, success=False, errors=["Invalid credentials."]) 
        return Utils.create_response(data=data)
    except Exception as e:
        logging.error(e)
        return Utils.create_response(status_code=400, success=False, errors=["Couldn't retrieve the tests status."]) 


@router.get(
    "/gui/logs-and-metrics",
    tags=["gui"],
    summary="Get Testing Process Logs and Metrics",
    description="Gets all the logs and metrics of the testing process.",
)
async def get_testing_process_metrics_and_logs(
    test_id: int,
    db: Session = Depends(get_db)
):
    try:
        metrics_data = crud.get_metrics_dasboard(db, test_id)
        if not metrics_data:
            return Utils.create_response(status_code=403, success=False, errors=["Invalid credentials."]) 
        logs_data = crud.get_logs_dasboard(db, test_id)
        if not logs_data:
            return Utils.create_response(status_code=403, success=False, errors=["Invalid credentials."]) 
        
        return Utils.create_response(
            data={
                "metrics": [metrics.as_dict() for metrics in metrics_data],
                "logs": [logs.as_dict() for logs in logs_data]
            }
            )
    except Exception as e:
        logging.error(e)
        return Utils.create_response(status_code=400, success=False, errors=["Couldn't retrieve the tests status."]) 




@router.get(
    "/gui/test-console-log",
    tags=["gui"],
    summary="Get testing process console log",
    description="While running the testing pipeline on the CI/CD Agent, a console log is created. This endpoint retrieves it.",
    response_class=PlainTextResponse,
    responses={
        403: {
            "content": {
                "application/json": {
                    "example": {**Utils.response_dict,
                    "message": "",
                    "success": False,
                    "errors": ["Invalid credentials."]
                    }
                }
            }
        }
    }
)
async def get_testing_console_log(test_id: int, access_token: str, db: Session = Depends(get_db)):
    # get test instance information
    test_instance = crud.get_test_instance(db, test_id, access_token)
    if not test_instance:
        return Utils.create_response(status_code=403, success=False, errors=["Invalid credentials."])
    test_console_log = urlopen(f"ftp://{Constants.FTP_RESULTS_USER}:{Constants.FTP_RESULTS_PASSWORD}@{Constants.FTP_RESULTS_URL}/{test_instance.test_log_location}").read()
    test_console_log = test_console_log.decode('utf-8')
    return PlainTextResponse(content=test_console_log , headers={"Access-Control-Allow-Origin": "*"})
    

@router.get(
    "/gui/test-base-information",
    tags=["gui"],
    summary="Get test base information",
    description="Get test base information (NetApp id, Testbed, Starting Time, ...)",
)
async def get_test_base_information(test_id: int, access_token: str, db: Session = Depends(get_db)):
    try:
        data = crud.get_test_base_information(db, test_id, access_token)
        if not data:
            return Utils.create_response(status_code=403, success=False, errors=["Invalid credentials."]) 
        return Utils.create_response(data=data)
    except Exception as e:
        logging.error(e)
        return Utils.create_response(status_code=400, success=False, errors=["Couldn't retrieve the test base information."]) 


@router.get(
    "/gui/tests-performed",
    tags=["gui"],
    summary="Get the performed Robot Tests",
    description="Get the performed Robot Tests and their results.",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {**Utils.response_dict,
                    "message": "",
                    "data": test_info_schemas.TestResults(
                        id=1,  
                        test_instance=1,
                        description="Tests the bandwidth between to VNFs. The results are in bits/sec",
                        performed_test="test_1",
                        start_time="timestamp",
                        end_time="timestamp",
                        success=True
                    ).dict()}
                }
            }
        },
        403: {
            "content": {
                "application/json": {
                    "example": {**Utils.response_dict,
                    "message": "",
                    "success": False,
                    "errors": ["Invalid credentials."]
                    }
                }
            }
        },
        400: {
            "content": {
                "application/json": {
                    "example": {**Utils.response_dict,
                    "message": "",
                    "success": False,
                    "errors": ["Couldn't retrieve the test performed."]
                    }
                }
            }
        }
    }
)
async def get_tests_performed(test_id: int, access_token: str, db: Session = Depends(get_db)):
    try:
        test_instance = crud.get_test_instance(db, test_id, access_token)    
        

        data = []
        test_stages = crud.get_test_stages_with_status_for_test_instance(db, test_id)
        test_cases = crud.get_tests_of_test_instance(db, test_id, access_token)
        for test_stage, test_state_statuses in test_stages.items():
            # Get Console Log
            results_base_folder = f"{test_instance.netapp_id}-{test_instance.network_service_id}" +\
                f"-{test_id}-{test_stage.id}"
            test_console_log = "Not Available Yet"
            try:
                test_console_log = urlopen(
                    f"ftp://{Constants.FTP_RESULTS_USER}:{Constants.FTP_RESULTS_PASSWORD}" +\
                    f"@{Constants.FTP_RESULTS_URL}/{results_base_folder}/console_log.log"
                ).read()
                test_console_log = test_console_log.decode('utf-8')
            except Exception as e:
                print("Could not obatin Console Log")

            # Get Test Status
            test_state_statuses = [status.as_dict() for status in test_state_statuses]
            for test_state_status in test_state_statuses:
                test_state_status["state"] = test_state_status["state"].value

            test_stage_data = {
                "id":  test_stage.id,
                "testing_agent_id": test_stage.testing_agent_id,
                "network_qos_profile": test_stage.network_qos_profile,
                "pipeline": test_stage.jenkins_pipeline,
                "console_log": test_console_log,
                "statuses": test_state_statuses,
                "test_cases": [
                    test_case.as_dict()
                    for test_case in sorted(
                        test_cases,
                        key=lambda tc: tc.id
                    )
                    if test_case.test_stage == test_stage.id
                ]

            }
            data.append(test_stage_data)

        # Sort test stages
        data = sorted(data, key=lambda ts: ts["id"])
        if not data:
            return Utils.create_response(status_code=403, success=False, errors=["Invalid credentials."]) 
        return Utils.create_response(data=data)
    except Exception as e:
        logging.error(e)
        return Utils.create_response(status_code=400, success=False, errors=["Couldn't retrieve the test performed."]) 



@router.get(
    "/gui/test-output-file",
    tags=["gui"],
    summary="Get Test Output File",
    description="After the validation pipeline, several files are created by the Robot Framework. This endpoint retrieves these files",
)
async def get_test_output_file(test_id: int, stage_id: int, access_token: str, test_name: str, file_name: str, db: Session = Depends(get_db)):
    test_instance = crud.get_test_instance(db, test_id, access_token)
    results_base_folder = f"{test_instance.netapp_id}-{test_instance.network_service_id}" +\
        f"-{test_id}-{stage_id}"
    if not test_instance:
        return Utils.create_response(status_code=403, success=False, errors=["Invalid credentials."]) 
    test_console_log = urlopen(f"ftp://{Constants.FTP_RESULTS_USER}:{Constants.FTP_RESULTS_PASSWORD}@{Constants.FTP_RESULTS_URL}/{results_base_folder}/{test_name}/{file_name}").read()
    test_console_log = test_console_log.decode('utf-8')
    return HTMLResponse(content=test_console_log,  headers={"Access-Control-Allow-Origin": "*"})
