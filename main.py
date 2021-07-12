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
from routers import testbeds
from fastapi import FastAPI
import logging
import inspect
import sys
import os

# import from parent directory
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

# custom imports
from sql_app.database import SessionLocal, engine
from routers import testbeds, tests, nodes
import aux.constants as Constants
import utils.utils as Utils
from sql_app import models


# Logger
logging.basicConfig(
    format="%(module)-15s:%(levelname)-10s| %(message)s",
    level=logging.INFO
)

# Start Fast API
app = FastAPI()

# Load Routers
app.include_router(testbeds.router)
app.include_router(tests.router)
app.include_router(nodes.router)


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
    # Connect to Database
    try:
        models.Base.metadata.create_all(bind=engine)
    except Exception as e:
        logging.critical("Unable to connect to database. Exception:", e)
        exit(1)
    
    db = SessionLocal()
    # Load testbed info
    ret, message = Utils.load_testbeds_to_db(db, Constants.TESTBED_INFO_FILEPATH)
    if not ret:
        logging.critical(message)
        db.close()
        return exit(2)

    # Load test info
    ret, message = Utils.load_test_info(db, Constants.TEST_INFO_FILEPATH)
    if not ret:
        db.close()
        logging.critical(message)
        return exit(3)
        
    db.close()
    
    # Load Config
    ret, message = Constants.load_config()
    if not ret:
        logging.critical(message)
        return exit(4)
