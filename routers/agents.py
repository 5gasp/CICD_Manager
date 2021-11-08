#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Author: Rafael Direito (rdireito@av.it.pt)
# Date: 1st july 2021
# Last Update: 12th july 2021

# Description:
# Constains all the endpoints related to the CI/CD Agents

# generic imports
from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session
from sql_app import crud
from sql_app.database import SessionLocal
from sqlalchemy.orm import Session
from sql_app import crud
from sql_app.schemas import ci_cd_manager as ci_cd_manager_schemas
from typing import List
import logging
import inspect
import sys
import os

# import from parent directory
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

# custom imports
import aux.utils as Utils
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
    response_model=ci_cd_manager_schemas.CI_CD_Node, 
    tags=["agents"],
    summary="Register new CI/CD Agent",
    description="When the CI/CD Agent is deployed (via a VNF) it registers itself in the CI_CD_Manager, via this endpoint.",
)
def create_node(node: ci_cd_manager_schemas.CI_CD_Node_Create, db: Session = Depends(get_db)):
    db_ci_cd_node = crud.get_ci_cd_node_by_testbed(db, node.testbed_id)
    if db_ci_cd_node:
        db_ci_cd_node = crud.update_ci_cd_node(db, node=node)
        return Utils.create_response(success=True, message="Updated CI/CD Node", data=db_ci_cd_node.as_dict_without_password())

    db_ci_cd_node = crud.create_ci_cd_node(db=db, node=node)
    return Utils.create_response(success=True, message="Created CI/CD Node", data=db_ci_cd_node.as_dict_without_password())


@router.get(
    "/agents/all", 
    response_model=List[ci_cd_manager_schemas.CI_CD_Node], 
    tags=["agents"],
    summary="Get all CI/CD Agents",
    description="Using this endpoint is possible to obtain a list of all the CI/CD Agents.",
)
def get_nodes(skip: int = 0, limit: int = 500, db: Session = Depends(get_db)):
    ci_cd_nodes = crud.get_all_nodes(db, skip=skip, limit=limit)
    return Utils.create_response(success=True, message="Got all CI/CD Nodes", data=[n.as_dict_without_password() for n in ci_cd_nodes])

