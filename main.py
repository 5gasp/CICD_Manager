#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Author: Rafael Direito (rdireito@av.it.pt)
# Date: 7th june 2021
# Last Update: 10th june 2021

# Description:
# Constains the CI Manager API.
# Supported endpoints: list all testbeds and the available tests for each one, 
# submit new testing jobs, etc

# generic imports
from fastapi import FastAPI, File, Form, UploadFile
import requests
import random
import string
import yaml

# custom imports
from test_descriptor_validator import Test_Descriptor_Validator
from jenkins_wrapper import Jenkins_Wrapper
import constants as Constants

# start Fast API
app = FastAPI()

# __init__
@app.on_event("startup")
async def startup_event():
    # load test info
    Constants.load_test_info()
    # validate envs
    if not Constants.validate_envs():
        return exit(1)

    

@app.get("/testbeds/all")
async def all_testbeds():
    data = {"testbeds": list(Constants.TEST_INFO['tests'].keys())}
    return Constants.create_response(data=data)


@app.get("/tests/all")
async def all_tests():
    data = Constants.TEST_INFO
    return Constants.create_response(data=data)


@app.get("/tests/per-testbed")
async def tests_per_testbed(testbed: str):
    testbed_tests = Constants.TEST_INFO['tests'].get(testbed, None)
    if testbed_tests:
        data = {"tests": testbed_tests}
        return Constants.create_response(data=data)
    else:
        return Constants.create_response(status_code=400, success=False, errors=["The testbed you chose doesn't exist."])


@app.post("/tests/new")
async def new_test(test_descriptor: UploadFile = File(...), testbed: str = Form(...),):
    # get data from the uploaded descriptor
    contents = await test_descriptor.read()
    try:
        test_descriptor_data = yaml.safe_load(contents.decode("utf-8"))
    except:
        return Constants.create_response(status_code=400, success=False, errors=["Unable to parse the submited file. It must be a YAML."])

    # check if the tesbed exists
    testbed_tests = Constants.TEST_INFO['tests'].get(testbed)
    if not testbed_tests:
        return Constants.create_response(status_code=400, success=False, errors=["The testbed you chose doesn't exist."])

    # check if the tests on the descriptor are well defined
    errors = []
    for test_name, test_info in test_descriptor_data["tests"].items():
        ok, error_message = Test_Descriptor_Validator.is_test_description_valid(test_name, test_info, testbed_tests)
        if not ok:
            errors.append(error_message)
    if len(errors) != 0:
        return Constants.create_response(status_code=400, success=False, errors=errors)

    # create jenkins connection
    jenkins_wrapper = Jenkins_Wrapper()

    # connect to jenkins server
    ret, message = jenkins_wrapper.connect_to_server(Constants.JENKINS_URL, Constants.JENKINS_USER, Constants.JENKINS_PASSWORD)
    if not ret:
        return Constants.create_response(status_code=400, success=False, errors=[message])

    # create jenkins job
    job_name = ''.join(random.choice(string.ascii_lowercase) for i in range(10))
    ret, message = jenkins_wrapper.create_new_job(job_name, test_descriptor_data["tests"], testbed_tests)
    if not ret:
        return Constants.create_response(status_code=400, success=False, errors=[message])
    jenkins_job_name = message
    
    # run jenkins job
    ret, message = jenkins_wrapper.run_job(jenkins_job_name)
    if not ret:
        return Constants.create_response(status_code=400, success=False, errors=[message])
    build_id = message

    return Constants.create_response(success=True, data=[f"A new job with the name '{jenkins_job_name}'' was created and a build job was started with the id '{build_id}'"])





    
   

    


