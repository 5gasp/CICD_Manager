#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Author: Rafael Direito (rdireito@av.it.pt)
# Date: 7th june 2021
# Last Update: 12th july 2021

# Description:
# Definition of information schemas to simplify the usage of the API endpoints.



# generic imports
from typing import List
from pydantic import BaseModel, Field
import datetime

# ---------------------------------------- #
# -------------- CI/CD Agents ------------- #
# ---------------------------------------- #
class CI_CD_Agent_Base(BaseModel):
    url: str = Field(..., example="http://my.cicd.agent")
    username: str = Field(..., example="username")
    testbed_id: str = Field(..., example="testbed_xyz")
    is_online: bool


class CI_CD_Agent_Create(CI_CD_Agent_Base):
    password: str = Field(..., example="password")
    

class CI_CD_Agent(CI_CD_Agent_Base):
    id: int
    communication_token: str

    class Config:
        orm_mode = True



# ---------------------------------------- #
# --------------- Testbeds --------------- #
# ---------------------------------------- #
class Testbed_Base(BaseModel):
    name: str = Field(..., example="XYZ Testbed")
    description: str = None

class Testbed_Create(Testbed_Base):
    id: str = Field(..., example="testbed_xyz")

class Testbed(Testbed_Base):
    id: str = Field(..., example="testbed_xyz")
    class Config:
        orm_mode = True




# ---------------------------------------- #
# ------------ Test Instances ------------ #
# ---------------------------------------- #

class Test_Instance_Base(BaseModel):
    netapp_id: str
    network_service_id: str
    build: int
    testbed_id: str
    ci_cd_node_id: int

class Test_Instance(Test_Instance_Base):
    id: str
    
    class Config:
        orm_mode = True


# ---------------------------------------- #
# -------------- Test Status ------------- #
# ---------------------------------------- #

class Test_Status_Base(BaseModel):
    test_id: int = Field(..., example=1)
    state: str = Field(..., example="ENVIRONMENT_SETUP_CI_CD_AGENT")
    success: bool

class Test_Status_Update(Test_Status_Base):
    communication_token: str

class Test_Status(Test_Status_Base):
    id: int
    timestamp: datetime.datetime
    
    class Config:
        orm_mode = True


# ---------------------------------------- #
# -------------- Test Results ------------ #
# ---------------------------------------- #

class Test_Results(BaseModel):
    test_id: int
    ftp_results_directory: str
    communication_token: str

    class Config:
        orm_mode = True