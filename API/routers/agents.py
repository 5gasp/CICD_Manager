#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Author: Rafael Direito (rdireito@av.it.pt)
# Date: 1st july 2021
# Last Update: 16th november 2021

# Description:
# Constains all the endpoints related to the CI/CD Agents

# generic imports
from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy.orm import Session
from typing import List
import logging
import inspect
import sys
import os

from starlette.types import Message

# custom imports
import sql_app.CRUD.agents as CRUD_Agents
import sql_app.CRUD.auth as CRUD_Auth
from sql_app.database import SessionLocal
from sql_app.schemas import ci_cd_manager as ci_cd_manager_schemas
from http import HTTPStatus
from aux import auth
from exceptions.auth import *
import aux.utils as Utils
from wrappers.jenkins.wrapper import Jenkins_Wrapper

# import from parent directory
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

# start the router
router = APIRouter()


# Logger
logging.basicConfig(
    format="%(module)-20s:%(levelname)-15s| %(message)s",
    level=logging.INFO
)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/agents/new", 
    tags=["agents"],
    summary="Register new CI/CD Agent",
    description="This endpoint allows the registering of a new CI/CD Agent.",
)
def create_agent(agent: ci_cd_manager_schemas.CI_CD_Agent_Create, token: str = Depends(auth.oauth2_scheme), db: Session = Depends(get_db)):
    try:
        login_username = auth.get_current_user(token)
        roles = CRUD_Auth.get_user_roles(db, login_username)
        # check if operation was ordered by an admin
        if "ADMIN" not in roles:
            raise NotEnoughPrivileges(login_username, 'register_new_ci_cd_agent')
        # try to create a ci_cd_agent
        # check if the credentials are correct
        jenkins_wrapper = Jenkins_Wrapper()
        ret, message = jenkins_wrapper.connect_to_server(f"http://{agent.ip}:8080/", agent.username, agent.password)
        if not ret:
            return Utils.create_response(status_code=HTTPStatus.BAD_REQUEST, success=False, errors=["Could not establish a connection with the CI/CD Agent - " + message]) 

        db_ci_cd_agent = CRUD_Agents.create_ci_cd_agent(db=db, agent=agent)
        return Utils.create_response(status_code=HTTPStatus.CREATED, success=True, message="Created CI/CD Agent", data=db_ci_cd_agent.as_dict_without_password())
    except Exception as e:
        logging.error(e)
        return Utils.create_response(status_code=e.status_code, success=False, errors=[e.message]) 


@router.delete(
    "/agents/delete/{agent_id}", 
    tags=["agents"],
    summary="Delete CI/CD Agent",
    description="Delete a CI/CD given its Id",
)
def delete_agent(agent_id: int, token: str = Depends(auth.oauth2_scheme), db: Session = Depends(get_db)):
    try:
        login_username = auth.get_current_user(token)
        roles = CRUD_Auth.get_user_roles(db, login_username)
        # check if operation was ordered by an admin
        if "ADMIN" not in roles:
            raise NotEnoughPrivileges(login_username, 'delete_ci_cd_agent')
        # try to create a ci_cd_agent
        CRUD_Agents.delete_ci_cd_agent(db=db, agent_id=agent_id)
        return Utils.create_response(status_code=HTTPStatus.OK, success=True, message="Deleted CI/CD Agent")
    except Exception as e:
        logging.error(e)
        return Utils.create_response(status_code=e.status_code, success=False, errors=[e.message]) 


@router.get(
    "/agents/all", 
    response_model=List[ci_cd_manager_schemas.CI_CD_Agent], 
    tags=["agents"],
    summary="Get all CI/CD Agents",
    description="Using this endpoint is possible to obtain a list of all the CI/CD Agents.",
)
def get_agents(skip: int = 0, limit: int = 500, token: str = Depends(auth.oauth2_scheme), db: Session = Depends(get_db)):
    try:
        login_username = auth.get_current_user(token)
        roles = CRUD_Auth.get_user_roles(db, login_username)
        # check if operation was ordered by an admin
        if "ADMIN" not in roles:
            raise NotEnoughPrivileges(login_username, 'register_new_user')
        ci_cd_nodes = CRUD_Agents.get_all_nodes(db, skip=skip, limit=limit)
        return Utils.create_response(success=True, message="Got all CI/CD Nodes", data=[n.as_dict_without_password() for n in ci_cd_nodes])
    except Exception as e:
        logging.error(e)
        return Utils.create_response(status_code=401, success=False, errors=[e.message]) 
