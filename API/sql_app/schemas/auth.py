#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Author: Rafael Direito (rdireito@av.it.pt)
# Date: 13th November 2021
# Last Update: 13th November 2021

# Description:
# Definition of information schemas to simplify the usage of the auth endpoints.



# generic imports
from typing import List
from pydantic import BaseModel
import datetime

class UserLogin(BaseModel):
    username: str
    password: str

class UserRegister(BaseModel):
    username: str
    password: str
    roles: List[str]

class Token(BaseModel):
    access_token: str
    token_type: str

class NewPassword(BaseModel):
    new_password: str

class UserInfo(BaseModel):
    username: str
    is_active: str
    roles: str
