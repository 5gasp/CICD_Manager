#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Author: Rafael Direito (rdireito@av.it.pt)
# Date: 7th june 2021
# Last Update: 10th june 2021

#
# Description:
# Contains several constant variables needed in the worlflow of the 
# CI/CD Manage

# generic imports
import configparser
import yaml
import os

# custom imports
from fastapi.responses import JSONResponse

# TEST INFO
TEST_INFO = None
TEST_INFO_FILEPATH = "static/test_information.yaml"

# PIPELINE INFO
BASE_PIPELINE_FILEPATH = "static/pipeline.xml"

# FTP
FTP_USER = None
FTP_PASSWORD = None
FTP_URL = None


JENKINS_BASE_PIPELINE_SCRIPT = """
pipeline {
    agent any
    stages {
        stage('Setup environment') {
            steps {
                <setup_environment>
            }
        }
        stage('Obtain Tests') {
            environment {
                <obtain_tests_environment>
            }  
            steps {
                <obtain_tests>
            }
        }
        stage('Perform Tests') {
            environment {
                <perform_tests_environment>
            }   
            steps {
                <perform_tests>
            }
        }
        stage('Logs') {
            steps {
                <logs_creation>
            }
        }
    }
}"""

def load_config():
    global FTP_USER, FTP_PASSWORD, FTP_URL

    # load config
    config = configparser.ConfigParser()
    config.read('config.ini')

    # Test config
    if not config['FTP']['User'] or not config['FTP']['Password'] or not config['FTP']['Url']:
        print(""" The config file should have an FTP section with the following variables
     - User
     - Password
     - Url
        """)
        return False

    # Load Variables
    FTP_USER = config['FTP']['User']
    FTP_PASSWORD = config['FTP']['Password']
    FTP_URL = config['FTP']['Url']
    return True
    
    
def load_test_info():
    global TEST_INFO
    with open(TEST_INFO_FILEPATH) as mfile:
        TEST_INFO = yaml.load(mfile, Loader=yaml.FullLoader)


def create_response(status_code=200, data=[], errors=[], success=True, message=""):
    return JSONResponse(status_code=status_code, content={"message":message, "success":success, "data":data, "errors":errors})
