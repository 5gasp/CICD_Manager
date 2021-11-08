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
from routers import testbeds, tests, agents, gui, tmf653_endpoints
import aux.constants as Constants
import aux.startup as Startup
import aux.utils as Utils
from sql_app import models
import wrappers.jenkins.constants as JenkinsConstants



# Logger
logging.basicConfig(
    format="%(module)-15s:%(levelname)-10s| %(message)s",
    level=logging.INFO
)

fast_api_tags_metadata = [
    {
        "name": "agents",
        "description": "Operations related with the CI/CD Agents.",
    },
    {
        "name": "tests",
        "description": "Operations related with the tests performed on the NetApps.",
    },
    {
        "name": "testbeds",
        "description": "Operations related with the testbeds.",
    },
    {
        "name": "gui",
        "description": "Endpoints provided to the GUI.",
    }
]

fast_api_description = "REST API of the 5GASP CI_CD_Manager"

# Start Fast API
app = FastAPI(
    title="5GASP CI_CD_Manager",
    description=fast_api_description,
    version="0.0.1",
    contact={
        "name": "Rafael Direito",
        "email": "rdireito@av.it.pt",
    },
    openapi_tags=fast_api_tags_metadata
)

# Load Routers
app.include_router(testbeds.router)
app.include_router(tests.router)
app.include_router(agents.router)
app.include_router(gui.router)
app.include_router(tmf653_endpoints.router)

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

    # Load Config
    ret, message = Startup.load_config()
    if not ret:
        logging.critical(message)
        return exit(1)

    # Connect to Database
    try:
        models.Base.metadata.create_all(bind=engine)
    except Exception as e:
        logging.critical("Unable to connect to database. Exception:", e)
        exit(2)
    
    db = SessionLocal()
    # Load testbed info
    ret, message = Utils.load_testbeds_to_db(db, Constants.TESTBED_INFO_FILEPATH)
    if not ret:
        logging.critical(message)
        db.close()
        return exit(3)

    ret, message = Utils.load_testbeds_info(Constants.TESTBED_INFO_FILEPATH)
    if not ret:
        logging.critical(message)
        db.close()
        return exit(3)

    # Load test info
    ret, message = Utils.load_test_info(db, Constants.TEST_INFO_FILEPATH)
    if not ret:
        db.close()
        logging.critical(message)
        return exit(4)

    # Load metrics collection info
    ret, message = Startup.load_metrics_collection_info()
    if not ret:
        db.close()
        logging.critical(message)
        return exit(5)
    
    # Load Jenkins Pipeline
    try:
        JenkinsConstants.BASE_PIPELINE = open(JenkinsConstants.BASE_PIPELINE_FILEPATH).read()
    except Exception as e:
        logging.critical(3)
        db.close()
        return exit(6)