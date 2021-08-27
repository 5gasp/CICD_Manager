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
from fastapi import APIRouter
from fastapi import Depends
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
from utils import utils as Utils
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
)
async def all_testbeds(db: Session = Depends(get_db)):
    data = {"testbeds": [t.as_dict() for t in crud.get_all_testbeds(db)]}
    return Utils.create_response(data=data)
