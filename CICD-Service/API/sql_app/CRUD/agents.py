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
import datetime

from sqlalchemy.orm import Session

# custom imports
from .. import models
from sql_app.schemas import ci_cd_manager as ci_cd_manager_schemas
from aux import auth
from exceptions.auth import *
from exceptions.agents import *
# Logger
logging.basicConfig(
    format="%(module)-15s:%(levelname)-10s| %(message)s",
    level=logging.INFO
)


def create_ci_cd_agent(db: Session, agent: ci_cd_manager_schemas.CI_CD_Agent_Create):
    db_ci_cd_agent = db.query(models.CI_CD_Agent).filter(models.CI_CD_Agent.url == agent.url, models.CI_CD_Agent.testbed_id == agent.testbed_id).first()

    if db_ci_cd_agent:
        raise AgentAlreadyExists(db_ci_cd_agent.id, db_ci_cd_agent.url, db_ci_cd_agent.username,  db_ci_cd_agent.testbed_id)
    db_ci_cd_agent = models.CI_CD_Agent(url=agent.url, username=agent.username, password=agent.password,
                                     testbed_id=agent.testbed_id,
                                      is_online=agent.is_online)
    db.add(db_ci_cd_agent)
    db.commit()
    db.refresh(db_ci_cd_agent)
    logging.info(f"Created CI/CD Agent with Id {db_ci_cd_agent.id}")
    return db_ci_cd_agent


def create_custom_ci_cd_agent(
        db: Session,
        testbed_id: str,
        service_order: str,
        name: str,
        test_instance_id: int,
        provisioning_started_time: datetime.datetime
    ):
    db_ci_cd_agent = models.CI_CD_Agent(
        testbed_id=testbed_id,
        type=models.AgentType.CUSTOM,
        service_order=service_order,
        name=name,
        test_instance=test_instance_id,
        provisioning_started_time = provisioning_started_time
    )
    db.add(db_ci_cd_agent)
    db.commit()
    db.refresh(db_ci_cd_agent)
    logging.info(f"Created Custom CI/CD Agent with Id {db_ci_cd_agent.id}")
    return db_ci_cd_agent

def update_custom_ci_cd_agent(
    db: Session,
    # Fields used for filtering
    test_instance_id: int,
    service_order: str,
    # Fields used for updates
    url: str,
    username: str,
    password: str,
    provisioning_finished_time: datetime.datetime
):
    db_ci_cd_agent = db.query(models.CI_CD_Agent).filter(
        models.CI_CD_Agent.test_instance == test_instance_id,
        models.CI_CD_Agent.service_order == service_order,
        models.CI_CD_Agent.type == models.AgentType.CUSTOM
    ).first()

    db_ci_cd_agent.url = url
    db_ci_cd_agent.username = username
    db_ci_cd_agent.password = password
    db_ci_cd_agent.provisioning_finished_time = provisioning_finished_time
    db.commit()
    db.refresh(db_ci_cd_agent)
    logging.info(f"Updated Custom CI/CD Agent with id {db_ci_cd_agent.id}")
    return db_ci_cd_agent

def get_custom_ci_cd_agents_for_test_instance(
    db: Session,
    test_instance_id: int,
):
    return db.query(models.CI_CD_Agent).filter(
        models.CI_CD_Agent.test_instance == test_instance_id,
        models.CI_CD_Agent.type == models.AgentType.CUSTOM
    ).all()



def delete_ci_cd_agent(db: Session, agent_id: int):
    db_ci_cd_agent = db.query(models.CI_CD_Agent).filter(models.CI_CD_Agent.id == agent_id).first()
    if not db_ci_cd_agent:
        raise AgentDoesNotExist(id)
    # set the test_instances agent to null
    for test_instance in db.query(models.Test_Instance).filter(
        models.Test_Instance.ci_cd_node_id == db_ci_cd_agent.id).all():
        test_instance.ci_cd_node_id = None
    db.delete(db_ci_cd_agent)
    db.commit()
    logging.info(f"Deleted CI/CD Agent with Id {db_ci_cd_agent.id}")

def get_custom_ci_cd_agents(db: Session):
    return db.query(models.CI_CD_Agent).filter(
        models.CI_CD_Agent.type == models.AgentType.CUSTOM
    ).all()

def get_ci_cd_node_by_id(db: Session, id: int):
    return db.query(models.CI_CD_Agent).filter(models.CI_CD_Agent.id == id).first()


def get_ci_cd_agents_by_testbed(db: Session, testbed_id: str):
    testbed_id =  db.query(models.Testbed).filter(models.Testbed.id == testbed_id).first().id
    if not testbed_id: return None
    return db.query(models.CI_CD_Agent).filter(models.CI_CD_Agent.testbed_id == testbed_id).all()


def get_all_nodes(db: Session, skip: int = 0, limit: int = 500):
    return db.query(models.CI_CD_Agent).offset(skip).limit(limit).all()


def update_communication_token(db: Session, id: int, token: str):
    db_ci_cd_node = db.query(models.CI_CD_Agent).filter(models.CI_CD_Agent.id == id).first()
    db_ci_cd_node.communication_token = token
    db.commit()
    db.refresh(db_ci_cd_node)
    logging.info(f"Updated ci_cd_nodes communication token on CI/CD Agent with id {db_ci_cd_node.id}")
    return db_ci_cd_node