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
from fastapi import Depends, FastAPI, HTTPException
from sql_app.database import SessionLocal, engine
from sqlalchemy.orm import Session
from sql_app import crud, models, schemas
from sql_app.database import SessionLocal, engine
import requests
import random
import string
import yaml
import json
from typing import List


# custom imports


# start Fast API
models.Base.metadata.create_all(bind=engine)
app = FastAPI()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# __init__
@app.on_event("startup")
async def startup_event():
    # load test info
    Constants.load_test_info()
    # load config
    if not Constants.load_config():
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
async def new_test(test_descriptor: UploadFile = File(...), testbed: str = Form(...), service_id: str = Form(...), db: Session = Depends(get_db)):
    global nodes
    # get data from the uploaded descriptor
    contents = await test_descriptor.read()
    try:
        test_descriptor_data = yaml.safe_load(contents.decode("utf-8"))
    except:
        return Constants.create_response(status_code=400, success=False, errors=["Unable to parse the submited file. It must be a YAML."])

    # Check if the CI/CD Node for this test is already running
    selected_ci_cd_node = crud.get_ci_cd_node_by_service_id(db, service_id=service_id)
    if selected_ci_cd_node is None:
        return Constants.create_response(status_code=400, success=False, errors=[f"It doesnt exist a CI/CD node for the servicce_id {service_id}"])

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
    ret, message = jenkins_wrapper.connect_to_server(f"http://{selected_ci_cd_node.ip}:8080/", selected_ci_cd_node.username,selected_ci_cd_node.password)
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

    return Constants.create_response(success=True, message=f"A new build job was created", data={"job_name":jenkins_job_name, "build_id":build_id})


@app.post("/nodes/new", response_model=schemas.CI_CD_Node)
def create_node(node: schemas.CI_CD_Node_Create, db: Session = Depends(get_db)):
    db_ci_cd_node = crud.get_ci_cd_node_by_service_id(db, service_id=node.service_id)
    if db_ci_cd_node:
        db_ci_cd_node = crud.update_ci_cd_node(db, node=node)
        return Constants.create_response(success=True, message="Updated CI/CD Node", data=db_ci_cd_node.as_dict_without_password())

    db_ci_cd_node = crud.create_ci_cd_node(db=db, node=node)
    return Constants.create_response(success=True, message="Created CI/CD Node", data=db_ci_cd_node.as_dict_without_password())


@app.get("/nodes/all", response_model=List[schemas.CI_CD_Node])
def get_nodes(skip: int = 0, limit: int = 500, db: Session = Depends(get_db)):
    ci_cd_nodes = crud.get_all_nodes(db, skip=skip, limit=limit)
    return Constants.create_response(success=True, message="Got all CI/CD Nodes", data=[n.as_dict_without_password() for n in ci_cd_nodes])


'''
@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@app.get("/users/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.post("/users/{user_id}/items/", response_model=schemas.Item)
def create_item_for_user(
    user_id: int, item: schemas.ItemCreate, db: Session = Depends(get_db)
):
    return crud.create_user_item(db=db, item=item, user_id=user_id)


@app.get("/items/", response_model=List[schemas.Item])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = crud.get_items(db, skip=skip, limit=limit)
    return items
   


'''
