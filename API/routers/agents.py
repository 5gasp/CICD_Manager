# -*- coding: utf-8 -*-
# @Author: Rafael Direito
# @Date:   22-05-2022 10:25:05
# @Email:  rdireito@av.it.pt
# @Last Modified by:   Rafael Direito
# @Last Modified time: 24-05-2022 11:17:36
# @Description: 


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
import binascii

from starlette.types import Message

# custom imports
import sql_app.CRUD.agents as CRUD_Agents
import sql_app.CRUD.auth as CRUD_Auth
from sql_app import crud
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
    responses={
        201: {
            "content": {
                "application/json": {
                    "example": {**Utils.response_dict,
                    "message": "Created CI/CD Agent",
                    "data": ci_cd_manager_schemas.CI_CD_Agent(
                        url="http://my.cicd.agent",
                        username="username",
                        testbed_id="testbed_xyz",
                        is_online=True,
                        id=1,
                        communication_token="abcd1234"
                        ).dict()}
                }
            }
        },
        400: {
            "content": {
                "application/json": {
                    "example": {**Utils.response_dict,
                    "message": "",
                    "success": False,
                    "errors": ["Could not establish a connection with the CI/CD Agent",
                    "A testbed with the id tesbed_itav does not exist"]}
                }
            }
        },
        401: {
            "content": {
                "application/json": {
                    "example": {**Utils.response_dict,
                    "message": "",
                    "success": False,
                    "errors": ["User does not have permission to perform this action"]}
                }
            }
        }
    }
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
        ret, message = jenkins_wrapper.connect_to_server(agent.url, agent.username, agent.password)
        if not ret:
            return Utils.create_response(status_code=HTTPStatus.BAD_REQUEST, success=False, errors=["Could not establish a connection with the CI/CD Agent - " + message]) 
        testbed_instance = crud.get_testbed_by_id(db=db,id=agent.testbed_id)

        if not testbed_instance:
            return Utils.create_response(status_code=HTTPStatus.BAD_REQUEST, success=False, errors=[f"A testbed with the id {agent.testbed_id} does not exists"]) 
        db_ci_cd_agent = CRUD_Agents.create_ci_cd_agent(db=db, agent=agent)
        
        # create jenkins  credentials
        credential_id = "communication_token"
        credential_secret = binascii.b2a_hex(os.urandom(16)).decode('ascii')
        credential_description = "Token used for communication with the CI/CD Manager"
        ret, message = jenkins_wrapper.create_credential(
            credential_id, credential_secret, credential_description)
        if not ret:
            return Utils.create_response(status_code=400, success=False, errors=[message])

        # update communication credential on db
        CRUD_Agents.update_communication_token(db, db_ci_cd_agent.id, credential_secret)
        
        return Utils.create_response(status_code=HTTPStatus.CREATED, success=True, message="Created CI/CD Agent", data=db_ci_cd_agent.as_dict_without_password())
    except Exception as e:
        logging.error(e)
        return Utils.create_response(status_code=HTTPStatus.BAD_REQUEST, success=False, errors=[str(e)]) 


@router.delete(
    "/agents/delete/{agent_id}", 
    tags=["agents"],
    summary="Delete CI/CD Agent",
    description="Delete a CI/CD given its Id",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {**Utils.response_dict,
                    "message": "Deleted CI/CD Agent",
                }
            }
        }
     },
        401: {
            "content": {
                "application/json": {
                    "example": {**Utils.response_dict,
                    "message": "",
                    "success": False,
                    "errors": ["User does not have permission to perform this action"]}
                }
            }
        }
    }
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
        return Utils.create_response(status_code=HTTPStatus.BAD_REQUEST, success=False, errors=[e])


@router.get(
    "/agents/all", 
    response_model=List[ci_cd_manager_schemas.CI_CD_Agent], 
    tags=["agents"],
    summary="Get all CI/CD Agents",
    description="Using this endpoint is possible to obtain a list of all the CI/CD Agents.",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {**Utils.response_dict,
                    "message": "Got all CI/CD Nodes",
                    "data": [ci_cd_manager_schemas.CI_CD_Agent(
                        url="http://my.cicd.agent",
                        username="username",
                        testbed_id="testbed_xyz",
                        is_online=True,
                        id=1,
                        communication_token="abcd1234"
                        ).dict()]
                }
            }
        }
     },
        401: {
            "content": {
                "application/json": {
                    "example": {**Utils.response_dict,
                    "message": "",
                    "success": False,
                    "errors": ["User does not have permission to perform this action"]}
                }
            }
        }
    }
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

