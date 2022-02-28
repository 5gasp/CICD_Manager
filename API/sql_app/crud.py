#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Author: Rafael Direito (rdireito@av.it.pt)
# Date:  7th june 2021
# Last Update: 12th july 2021

# Description:
# Contains all the CRUD operations over the Database


import logging
import random
import string
# generic imports
from os import access

from sqlalchemy.orm import Session

# custom imports
from . import models
from sql_app.schemas import ci_cd_manager as ci_cd_manager_schemas
from aux import auth
from sql_app.CRUD import agents as agents_crud
from exceptions.auth import *
from exceptions.agents import *
# Logger
logging.basicConfig(
    format="%(module)-15s:%(levelname)-10s| %(message)s",
    level=logging.INFO
)

# ---------------------------------------- #
# --------------- Testbeds --------------- #
# ---------------------------------------- #

def create_testbed(db: Session, testbed: ci_cd_manager_schemas.Testbed_Base):
    testbed_instance = models.Testbed(name=testbed.name, description=testbed.description)
    db.add(testbed_instance)
    db.commit()
    db.refresh(testbed_instance)
    logging.info(f"Created testbed with id {testbed_instance.id}")
    return testbed_instance


def create_testbed(db: Session, testbed_id: int, testbed_name: str, testbed_description: str):
    testbed_instance = models.Testbed(id=testbed_id, name=testbed_name, description=testbed_description)
    db.add(testbed_instance)
    db.commit()
    db.refresh(testbed_instance)
    logging.info(f"Created testbed with id {testbed_instance.id}")
    return testbed_instance


def get_testbed_by_id(db: Session, id: str):
    return db.query(models.Testbed).filter(models.Testbed.id == id).first()


def get_testbed_by_name(db: Session, testbed_name: str):
    return db.query(models.Testbed).filter(models.Testbed.name == testbed_name).first()


def get_all_testbeds(db: Session, skip: int = 0, limit: int = 500):
    return db.query(models.Testbed).offset(skip).limit(limit).all()



# ---------------------------------------- #
# ------------ Test Instances ------------ #
# ---------------------------------------- #

def create_test_instance(db: Session, netapp_id: str, network_service_id: str, testbed_id: str, extra_information: str = None, nods_id:str = None):
    current_build = get_last_build_of_test_instance(db, netapp_id, network_service_id) + 1
    test_instance = models.Test_Instance(netapp_id=netapp_id, network_service_id=network_service_id, build=current_build, testbed_id=testbed_id, access_token=''.join(random.choice(string.ascii_lowercase) for i in range(16)))
    if extra_information:
        test_instance.extra_information = extra_information
    if nods_id:
        test_instance.nods_id = nods_id
    db.add(test_instance)
    db.commit()
    db.refresh(test_instance)
    logging.info(f"Created test instance for netapp_id '{netapp_id}' and network_service_id '{network_service_id}'.")
    return test_instance


def update_test_instance_extra_info(db: Session, test_id: int, extra_information: str):
    db_test_instance = db.query(models.Test_Instance).filter(models.Test_Instance.id == test_id).first()
    db_test_instance.extra_information = extra_information
    db.commit()
    db.refresh(db_test_instance)
    logging.info(f"Updated extra information on test instance {db_test_instance.id}.")
    return db_test_instance


def get_test_instance(db: Session, test_id: int, access_token: str = None):
    if access_token is None:
        db_test_instance = db.query(models.Test_Instance).filter(models.Test_Instance.id == test_id).first()
    else:
        db_test_instance = db.query(models.Test_Instance).filter(models.Test_Instance.id == test_id, models.Test_Instance.access_token == access_token).first()
    return db_test_instance


def update_test_instance_ci_cd_agent(db: Session, test_id: int, ci_cd_id: int):
    db_test_instance = db.query(models.Test_Instance).filter(models.Test_Instance.id == test_id).first()
    db_test_instance.ci_cd_node_id = ci_cd_id
    db.commit()
    db.refresh(db_test_instance)
    logging.info(f"Updated ci_cd_node agent on test instance {db_test_instance.id}.")
    return db_test_instance


def update_test_instance_after_validation_process(db: Session, test_id: int, test_log_location: str, test_results_location:str):
    db_test_instance = db.query(models.Test_Instance).filter(models.Test_Instance.id == test_id).first()
    db_test_instance.test_log_location = test_log_location
    db_test_instance.test_results_location = test_results_location
    db.commit()
    db.refresh(db_test_instance)
    logging.info(f"Updated test_results_location and test_log_location on test instance {db_test_instance.id}.")
    return db_test_instance
  

def get_test_instances_by_netapp_and_network_service(db: Session, netapp_id: str, network_service_id: str):
    return db.query(models.Test_Instance).filter(models.Test_Instance.netapp_id == netapp_id, models.Test_Instance.network_service_id == network_service_id).all()


def get_test_instances_by_id(db: Session, test_instance_id: int):
    return db.query(models.Test_Instance).filter(models.Test_Instance.id == test_instance_id).first().as_dict()


def get_last_build_of_test_instance(db: Session, netapp_id: str, network_service_id: str):
    return len(db.query(models.Test_Instance).filter(models.Test_Instance.netapp_id == netapp_id, models.Test_Instance.network_service_id == network_service_id).all())


def get_ci_cd_agent_given_test_instance_id(db: Session, test_instance_id: int):
    ci_cd_node_id = db.query(models.Test_Instance).filter(models.Test_Instance.id == test_instance_id).first().ci_cd_node_id
    return agents_crud.get_ci_cd_node_by_id(db, ci_cd_node_id)



# ---------------------------------------- #
# -------------- Test Status ------------- #
# ---------------------------------------- #

def create_test_status(db: Session, test_id: int, state: str, success: bool):
    test_status = models.Test_Status(test_id=test_id, state=state.upper(), success=success)
    db.add(test_status)
    db.commit()
    db.refresh(test_status)
    logging.info(f"Created test status: {test_status.as_dict()}")
    return test_status


def create_test_status_ci_cd_agent(db: Session, test_status: ci_cd_manager_schemas.Test_Status_Update):    
    # 1 - validate communication token
    if not is_communication_token_for_test_valid(db, test_status.test_id, test_status.communication_token):
        raise Exception("Communication Tokens don't match")
    # 2 - create status
    test_status = models.Test_Status(test_id=test_status.test_id, state=test_status.state.upper(), success=test_status.success)
    db.add(test_status)
    db.commit()
    db.refresh(test_status)
    logging.info(f"CI/CD Agent created test status: {test_status.as_dict()}")
    return test_status


def get_test_status_given_test_id(db: Session, test_id: int):
    return db.query(models.Test_Status).filter(models.Test_Status.test_id == test_id).all()


def get_all_test_status_for_test(db: Session, netapp_id: str, network_service_id: str):
    test_instances = get_test_instances_by_netapp_and_network_service(db, netapp_id, network_service_id)
    dic = {
        "netapp_id": netapp_id,
        "network_service_id": network_service_id,
        "test_status": {}
    }
    for t in test_instances:
        dic["test_status"]["Build " + str(t.build)] = [ts.as_dict() for ts in get_test_status_given_test_id(db, t.id)]
    return dic


def get_all_test_status_for_test_given_id(db: Session, test_id: int, access_token: str = None):
    if __validate_test_instance_access_token(db, test_id, access_token):
        db_test_instance = db.query(models.Test_Instance).filter(models.Test_Instance.id == test_id).first()
        test_status = get_test_status_given_test_id(db, test_id)
        return test_status



# ---------------------------------------- #
# ---------- Test Instance Tests --------- #
# ---------------------------------------- #

def create_test_instance_test(db: Session, test_instance_id: int, performed_test: str, description: str, performed_test_results_location: str = None):
    test_instance_test = models.Test_Instance_Tests(test_instance=test_instance_id, performed_test=performed_test, description=description)
    if performed_test_results_location:
        test_instance_test.performed_test_results_location = performed_test_results_location
    db.add(test_instance_test)
    db.commit()
    db.refresh(test_instance_test)
    logging.info(f"Test Instance Test created : {test_instance_test.as_dict()}")
    return test_instance_test


def update_test_instance_test(db: Session, test_instance_id: int, performed_test: str, description: str, performed_test_results_location: str = None):
    test_instance_test = db.query(models.Test_Instance_Tests).filter(models.Test_Instance_Tests.test_instance == test_instance_id and 
    models.Test_Instance_Tests.performed_test == performed_test).first()
    test_instance_test.performed_test_results_location = performed_test_results_location
    test_instance_test.description = description
    db.commit()
    db.refresh(test_instance_test)
    logging.info(f"Test Instance Test update : {test_instance_test.as_dict()}")
    return test_instance_test


def get_tests_of_test_instance(db: Session, test_instance_id: int, access_token: str = None):
    if __validate_test_instance_access_token(db, test_instance_id, access_token):
        test_instance_tests = db.query(models.Test_Instance_Tests).filter(models.Test_Instance_Tests.test_instance == test_instance_id).all()
        return test_instance_tests


def update_test_status_of_test_instance(db: Session, test_instance_id: int, performed_test: str, start_time: str, end_time: str, success: bool):
    test_instance_test = db.query(models.Test_Instance_Tests).filter(models.Test_Instance_Tests.test_instance == test_instance_id, 
    models.Test_Instance_Tests.performed_test == performed_test).first()
    test_instance_test.start_time = start_time
    test_instance_test.end_time = end_time
    test_instance_test.success = success
    db.commit()
    db.refresh(test_instance_test)
    logging.info(f"Test Instance Test update : {test_instance_test.as_dict()}")
    return test_instance_test



# ---------------------------------------- #
# ----------------- Utils ---------------- #
# ---------------------------------------- #

def is_communication_token_for_test_valid(db: Session, test_instance_id: int, communication_token: str):
    # 1 get the CI/CD Agent for the test instance
    db_test_instance = db.query(models.Test_Instance).filter(models.Test_Instance.id == test_instance_id).first()
    db_ci_cd_node = db.query(models.CI_CD_Agent).filter(models.CI_CD_Agent.id == db_test_instance.ci_cd_node_id).first()
    print(db_test_instance.as_dict())
    # 2 -check if the communication token is ok
    if db_ci_cd_node.communication_token != communication_token:
        return False
    return True


def get_test_base_information(db: Session, test_instance_id: int, access_token: str = None):
    data = {}
    if __validate_test_instance_access_token(db, test_instance_id, access_token):
        db_test_instance = db.query(models.Test_Instance).filter(models.Test_Instance.id == test_instance_id).first()      
        all_test_status = get_all_test_status_for_test_given_id(db, test_instance_id)
        starting_time = all_test_status[0].timestamp
        test_status = all([ts.success for ts in all_test_status])
        return {
            "test_id": db_test_instance.id,
            "netapp_id": db_test_instance.netapp_id,
            "network_service_id": db_test_instance.network_service_id,
            "testbed_id": db_test_instance.testbed_id,
            "started_at": str(starting_time),
            "test_status": test_status,
        }

def __validate_test_instance_access_token(db: Session, test_instance_id: int, access_token: str = None):
    if access_token is not None:
        db_test_instance = db.query(models.Test_Instance).filter(models.Test_Instance.id == test_instance_id, models.Test_Instance.access_token == access_token).first()   
        if not db_test_instance: 
            logging.info(f"Invalid access_token for test_instance_id {test_instance_id}.")
            return False
    return True