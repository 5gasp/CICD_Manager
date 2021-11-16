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

# ---------------------------------------- #
# -----------------  Auth  --------------- #
# ---------------------------------------- #

def create_role(db: Session, role: str):
    db_role = db.query(models.Role).filter(models.Role.role == role).first()
    if not db_role:
        db_role = models.Role(role=role)
        db.add(db_role)
        db.commit()
        db.refresh(db_role)
        logging.info(f"Role created : {db_role.as_dict()}")
    logging.info(f"Role {db_role.as_dict()} was already created")
    return db_role


def register_user(db: Session, username: str, password: str, roles: list[str]):
    # 1 - check if user already exists
    db_user = db.query(models.User).filter(models.User.username == username).first()   
    if db_user:
        logging.info(f"User {username} already exists - {db_user.as_dict()}")
        return db_user
    # 2 - hash the password
    hashed_password = auth.get_password_hash(password)

    # 3 - create db checkpoint
    checkpoint = db.begin_nested()
    try:
        # 3.1 - create user
        db_user =  models.User(username=username, hashed_password=hashed_password, is_active=True)
        db.add(db_user)
        db.commit()

        # 3.2 - create user roles
        db_user_roles = []
        for role in roles:
            # get role id
            db_role = db.query(models.Role).filter(models.Role.role == role.upper()).first()
            db_user_role = models.User_Role(user=db_user.id, role=db_role.id)
            db_user_roles.append(db_user_role)
        db.add_all(db_user_roles)
        db.commit()
        db.refresh(db_user)
    except:
        checkpoint.rollback()
        logging.info(f"Could not create user {username}")
        raise UserCreationFailed(username)
    
    logging.info(f"User {username} created with success")
    return db_user


def authenticate_user(db: Session, username: str, password: str):
    # 1 - check if credentials are correct
    try:
        user = db.query(models.User).filter(models.User.username == username).first()   
        if not auth.verify_password(password, user.hashed_password):
            raise UserInvalidCredentials(username)
    except:
        raise UserInvalidCredentials(username)
    # 2 - check if user is active
    if not user.is_active:
        raise UserNotActive(username)
    return user


def get_user_info(db: Session, username:str):
    try:
        db_user = db.query(models.User).filter(models.User.username == username).first() 
    except:
        raise InvalidUser(username)
    return {"username": db_user.username, "is_active": db_user.is_active, "roles": get_user_roles(db, username)}


def get_user_roles(db: Session, username:str):
    # 1 - check if user exists
    user = db.query(models.User).filter(models.User.username == username).first()   
    if not user:
        raise UserDoesNorExist(username)
    # 2 - get roles
    user_roles = db.query(models.User_Role).filter(models.User_Role.user == user.id).all()
    if len(user_roles) == 0:
        return set()
    # 3 - roles2str
    user_roles_str = []
    for user_role in user_roles:
        role = db.query(models.Role).filter(models.Role.id == user_role.role).first()
        user_roles_str.append(role.role)
    return user_roles_str
    

def update_user_password(db: Session, username: str, new_password: str):    
    try:
       # 1 - get user
        db_user = db.query(models.User).filter(models.User.username == username).first()   
        # 2 - hash the password and update the db
        hashed_password = auth.get_password_hash(new_password)
        db_user.hashed_password = hashed_password
        db.commit()
        db.refresh(db_user)
    except:
        logging.info(f"Could not update {username}'s passsword")
        raise PasswordUpdateFailed(username)
    
    logging.info(f"{username}'s password updated with success")
    return db_user

