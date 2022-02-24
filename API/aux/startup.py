#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Author: Daniel Gomes (dagomes@av.it.pt),
# Date: 19th october 2021
# Last Update: 19th october 2021

# Description:
# Contains several functions that should be invoked on startup

# custom imports
import aux.constants as Constants
from sql_app.CRUD import auth as CRUD_Auth

# generic imports
import configparser
import logging
import yaml
import os
import inspect

# Logger
logging.basicConfig(
    format="%(module)-15s:%(levelname)-10s| %(message)s",
    level=logging.INFO
)
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))


def load_config():
    # load config
    config = configparser.ConfigParser()
    config.read('config.ini')

    # Test config
    try:
        # Load Variables
        Constants.FTP_RESULTS_USER = config['FTP']['User']
        Constants.FTP_RESULTS_PASSWORD = config['FTP']['Password']
        Constants.FTP_RESULTS_URL = config['FTP']['Url']
        Constants.CI_CD_MANAGER_URL = config['CI_CD_MANAGER']['Url']
        Constants.TEST_INFO_FILEPATH = config['DESCRIPTORS_LOCATION']['Tests_Information_Descriptor_Filepath']
        Constants.TESTBED_INFO_FILEPATH = config['DESCRIPTORS_LOCATION']['Testbeds_Information_Descriptor_Filepath']
        Constants.METRICS_COLLECTION_INFO_FILEPATH = config['DESCRIPTORS_LOCATION']['Metrics_Collection_Information_Descriptor_Filepath']
        Constants.DB_LOCATION = config['DB']['Location']
        Constants.DB_NAME = config['DB']['Name']
        Constants.DB_USER = config['DB']['User']
        Constants.DB_PASSWORD = config['DB']['Password']
        Constants.MR_LOCATION = config['METRICS-REPOSITORY']['InfluxDB_Location']
        Constants.MR_DB = config['METRICS-REPOSITORY']['DB_Name']
        Constants.NODS_HOST = config['NODS']['Host']
        Constants.NODS_USER = config['NODS']['User']
        Constants.NODS_PASSWORD = config['NODS']['Password']
    except Exception as e:
        print(e)
        print("-----")
        return False, """The config file should have the folling sections with the following variables: 
        FTP -> User, Password, Url | CI_CD_MANAGER -> Url | DESCRIPTORS_LOCATION -> Tests_Information_Descriptor_Filepath, 
        Testbeds_Information_Descriptor_Filepath, Metrics_Collection_Information_Descriptor_Filepath | DB -> Location, 
        Name, User, Password | METRICS-REPOSITORY -> InfluxDB_Location, DB_Name"""
    return True, ""


def load_test_info():
    with open(Constants.TEST_INFO_FILEPATH) as file:
        TEST_INFO = yaml.load(file, Loader=yaml.FullLoader)


def load_metrics_collection_info():
    try:
        with open(Constants.METRICS_COLLECTION_INFO_FILEPATH) as file:
            Constants.METRICS_COLLECTION_INFO = yaml.load(file, Loader=yaml.FullLoader)
    except:
        return False, "Could not load the metrics collection information"
    return True, ""


def startup_roles(db):
    for role in Constants.USER_ROLES:
        CRUD_Auth.create_role(db, role)


def create_default_admin(db):
    CRUD_Auth.register_user(
        db = db, 
        username = Constants.DEFAULT_ADMIN_CREDENTIALS['username'], 
        password = Constants.DEFAULT_ADMIN_CREDENTIALS['password'],
        roles = Constants.USER_ROLES)