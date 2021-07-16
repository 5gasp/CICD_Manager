#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Author: Rafael Direito (rdireito@av.it.pt)
# Date:  7th june 2021
# Last Update: 12th july 2021

# Description:
# Contains all the CRUD operations over the Database


# generic imports
from sqlalchemy.orm import Session
import logging

# custom imports
from . import models, schemas

# Logger
logging.basicConfig(
    format="%(module)-15s:%(levelname)-10s| %(message)s",
    level=logging.INFO
)

# ---------------------------------------- #
# -------------- CI/CD Nodes ------------- #
# ---------------------------------------- #

def create_ci_cd_node(db: Session, node: schemas.CI_CD_Node_Create):
    db_ci_cd_node = models.CI_CD_Node(ip=node.ip, username=node.username, password=node.password, netapp_id=node.netapp_id, network_service_id=node.network_service_id,
                                     testbed_id=node.testbed_id,
                                      is_online=node.is_online)
    db.add(db_ci_cd_node)
    db.commit()
    db.refresh(db_ci_cd_node)
    logging.info(f"Created ci_cd_node with id {db_ci_cd_node.id}")
    return db_ci_cd_node


def update_ci_cd_node(db: Session, node: schemas.CI_CD_Node_Create):
    db_ci_cd_node = db.query(models.CI_CD_Node).filter( models.CI_CD_Node.netapp_id == node.netapp_id and models.CI_CD_Node.network_service_id == node.network_service_id).first()
    db_ci_cd_node.ip = node.ip
    db_ci_cd_node.username = node.username
    db_ci_cd_node.password = node.password
    db_ci_cd_node.testbed_id = node.testbed_id
    db_ci_cd_node.is_online = node.is_online
    db.commit()
    db.refresh(db_ci_cd_node)
    logging.info(f"Updated ci_cd_node with id {db_ci_cd_node.id}")
    return db_ci_cd_node


def get_ci_cd_node_by_id(db: Session, id: int):
    return db.query(models.CI_CD_Node).filter(models.CI_CD_Node.id == id).first()


def get_ci_cd_node_by_netapp_and_network_service(db: Session, netapp_id: str, network_service_id:str):
    return db.query(models.CI_CD_Node).filter(models.CI_CD_Node.netapp_id == netapp_id and models.CI_CD_Node.network_service_id == network_service_id).first()


def get_all_nodes(db: Session, skip: int = 0, limit: int = 500):
    return db.query(models.CI_CD_Node).offset(skip).limit(limit).all()

def update_communication_token(db: Session, id: int, token: str):
    db_ci_cd_node = db.query(models.CI_CD_Node).filter(models.CI_CD_Node.id == id).first()
    db_ci_cd_node.communication_token = token
    db.commit()
    db.refresh(db_ci_cd_node)
    logging.info(f"Updated ci_cd_nodes communication token on CI/CD Agent with id {db_ci_cd_node.id}")
    return db_ci_cd_node

# ---------------------------------------- #
# --------------- Testbeds --------------- #
# ---------------------------------------- #

def create_testbed(db: Session, testbed: schemas.Testbed_Base):
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

def create_test_instance(db: Session, netapp_id: str, network_service_id: str, testbed_id: str):
    current_build = get_last_build_of_test_instance(db, netapp_id, network_service_id) + 1
    test_instance = models.Test_Instance(netapp_id=netapp_id, network_service_id=network_service_id, build=current_build, testbed_id=testbed_id)
    db.add(test_instance)
    db.commit()
    db.refresh(test_instance)
    logging.info(f"Created test instance for netapp_id '{netapp_id}' and network_service_id '{network_service_id}'.")
    return test_instance

def update_ci_cd_agent(db: Session, test_id: int, ci_cd_id: int):
    db_test_instance = db.query(models.Test_Instance).filter(models.Test_Instance.id == test_id).first()
    db_test_instance.ci_cd_node_id = ci_cd_id
    db.commit()
    db.refresh(db_test_instance)
    logging.info(f"Updated ci_cd_node agent on test instance {db_test_instance.id}.")
    return db_test_instance


def get_test_instances_by_netapp_and_network_service(db: Session, netapp_id: str, network_service_id: str):
    return db.query(models.Test_Instance).filter(models.Test_Instance.netapp_id == netapp_id and models.Test_Instance.network_service_id == network_service_id).all()


def get_last_build_of_test_instance(db: Session, netapp_id: str, network_service_id: str):
    return len(db.query(models.Test_Instance).filter(models.Test_Instance.netapp_id == netapp_id and models.Test_Instance.network_service_id == network_service_id).all())




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

def create_test_status_ci_cd_agent(db: Session, test_status: schemas.Test_Status_Update):    
    # 1 get the CI/CD Agent for the test instance
    db_test_instance = db.query(models.Test_Instance).filter(models.Test_Instance.id == test_status.test_id).first()
    db_ci_cd_node = db.query(models.CI_CD_Node).filter(models.CI_CD_Node.id == db_test_instance.ci_cd_node_id).first()

    # 2 -check if the communication token is ok
    if db_ci_cd_node.communication_token != test_status.communication_token:
        raise Exception("Communication Tokens don't match")

    # 3 -create status
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
