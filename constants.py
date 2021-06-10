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
FTP_USER = os.getenv('FTP_USER', None)
FTP_PASSWORD = os.getenv('FTP_PASSWORD', None)
FTP_URL = os.getenv('FTP_URL', None)

# JENKINS
JENKINS_USER = os.getenv('JENKINS_USER', None)
JENKINS_PASSWORD = os.getenv('JENKINS_PASSWORD', None)
JENKINS_URL = os.getenv('JENKINS_URL', None)

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

def validate_envs():
    global JENKINS_USER, JENKINS_PASSWORD, JENKINS_URL, FTP_USER, FTP_PASSWORD, FTP_URL
    if not JENKINS_USER or not JENKINS_PASSWORD or not JENKINS_URL or not FTP_USER or not FTP_PASSWORD or not FTP_URL:
        print("""Please define all the mandatory environment variables:
     - JENKINS_USER
     - JENKINS_PASSWORD
     - JENKINS_URL
     - FTP_USER
     - FTP_PASSWORD
     - FTP_URL
        """)
        return False
    return True
    
def load_test_info():
    global TEST_INFO
    with open(TEST_INFO_FILEPATH) as mfile:
        TEST_INFO = yaml.load(mfile, Loader=yaml.FullLoader)


def create_response(status_code=200, data=[], errors=[], success=True):
    return JSONResponse(status_code=status_code, content={"data":data, "errors":errors, "success":success})
