#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Author: Rafael Direito (rdireito@av.it.pt)
# Date: 1st july 2021
# Last Update: 12th july 2021

# Description:
# Constains all the endpoints related to the testbeds

# generic imports
from sql_app.database import SessionLocal
from sqlalchemy.orm import Session
import sql_app.schemas.ci_cd_manager as Schemas 
import sql_app.models as Models
from fastapi import APIRouter
from fastapi import Depends
from fastapi import File, UploadFile
from sql_app import crud
import logging
import inspect
import sys
import os
# import from parent directory
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

# custom imports
from aux import utils as Utils
router = APIRouter()

# Logger
logging.basicConfig(
    format="%(module)-15s:%(levelname)-10s| %(message)s",
    level=logging.INFO
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get(
    "/testbeds/all", 
    tags=["testbeds"],
    summary="Get all testbeds",
    description="Get all the testbeds available.",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {**Utils.response_dict,
                    "data": Schemas.Testbed(name="ITAv Testbed",id="tesbed_itav").dict()}
                }
            }
        }
    }
)
async def all_testbeds(db: Session = Depends(get_db)):
    data = {"testbeds": [t.as_dict() for t in crud.get_all_testbeds(db)]}
    return Utils.create_response(data=data)

@router.post(
    "/testbeds",
    tags=["testbeds"],
    summary="Create a testbed on DB",
    responses={
        201: {
            "content": {
                "application/json": {
                    "example": {**Utils.response_dict,
                    "message": "Success creating new testbed",
                    "data": Schemas.Testbed(name="ITAv Testbed",id="tesbed_itav").dict()}
                }
            }
        },
        400: {
            "content": {
                "application/json": {
                    "example": {**Utils.response_dict,
                    "message": "",
                    "success": False,
                    "errors": ["A testbed with the id tesbed_itav already exists",
                    "A testbed with the name ITAv Testbed already exists"]}
                }
            }
        }
    }
)
async def create_testbed(testbedData: Schemas.Testbed_Create,db: Session = Depends(get_db)):
    testbed_instance = crud.get_testbed_by_id(db=db,id=testbedData.id)
    errors = []

    if testbed_instance:
        errors.append(f"A testbed with the id {testbedData.id} already exists")
    testbed_instance = crud.get_testbed_by_name(db=db,testbed_name=testbedData.name)

    if testbed_instance:
        errors.append(f"A testbed with the name {testbedData.name} already exists")
    if errors:
        return Utils.create_response(status_code=400, success=False,errors=errors)

    testbed_instance = crud.create_testbed(db,testbedData)
    return Utils.create_response(status_code=201,data=testbed_instance.as_dict(), message="Success creating new testbed")