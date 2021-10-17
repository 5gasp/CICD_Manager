#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Author: Rafael Direito (rdireito@av.it.pt)
# Date: 7th june 2021
# Last Update: 10th june 2021

#
# Description:
# Contains several constant variables needed in the workflow of the
# CI/CD Manage

# generic imports
import configparser
import logging
import yaml

# Logger
logging.basicConfig(
    format="%(module)-15s:%(levelname)-10s| %(message)s",
    level=logging.INFO
)


# CI/CD MANAGER 
CI_CD_MANAGER_URL = None

# TEST/TESTBED INFO
TEST_INFO = None
TEST_INFO_FILEPATH = "static/test_information.yaml"
TESTBED_INFO_FILEPATH = "static/testbeds_information.yaml"

# Metrics Collection Info
METRICS_COLLECTION_INFO = None
METRICS_COLLECTION_INFO_FILEPATH = "static/metrics_collection_information.yaml"

# PIPELINE INFO
BASE_PIPELINE_FILEPATH = "static/pipeline.xml"

# FTP
FTP_USER = None
FTP_PASSWORD = None
FTP_URL = None



TEST_STATUS ={
    "submitted_on_manager": "SUBMITTED_TO_CI_CD_MANAGER",
    "ci_cd_agent_provisioned": "PROVISIONED_CI_CD_AGENT",
    "ci_cd_agent_auth": "AUTHENTICATED_ON_CI_CD_AGENT",
    "created_comm_token": "CREATED_COMMUNICATION_TOKEN_ON_CI_CD_AGENT",
    "created_pipeline_script": "CREATED_PIPELINE_SCRIPT",
    "submitted_pipeline_script": "SUBMITTED_PIPELINE_SCRIPT",
    "ci_cd_agent_setup_environment": "ENVIRONMENT_SETUP_CI_CD_AGENT",
    "monitoring_started": "STARTED_MONITORING",
    "ci_cd_agent_obtained_tests": "OBTAINED_TESTS_ON_CI_CD_AGENT",
    "ci_cd_agent_performed_tests": "PERFORMED_TESTS_ON_CI_CD_AGENT",
    "ci_cd_agent_created_logs": "CREATED_LOGS_ON_CI_CD_AGENT",
    "monitoring_ended": "ENDED_MONITORING",
    "ci_cd_agent_published_test_results": "PUBLISHED_TEST_RESULTS",
    "ci_cd_agent_cleaned_test_environment": "CLEANED_TEST_ENVIRONMENT",
    "test_ended": "TEST_ENDED",
    "obtained_metrics_collection_files": "OBTAINED_METRICS_COLLECTION_FILES",
}

def load_config():
    global FTP_USER, FTP_PASSWORD, FTP_URL, CI_CD_MANAGER_URL

    # load config
    config = configparser.ConfigParser()
    config.read('config.ini')

    # Test config
    try:
        # Load Variables
        FTP_USER = config['FTP']['User']
        FTP_PASSWORD = config['FTP']['Password']
        FTP_URL = config['FTP']['Url']
        CI_CD_MANAGER_URL = config['CI_CD_MANAGER']['Url']
    except:
        return False, "The config file should have the folling sections with the following variables: FTP -> User, Password, Url | CI_CD_MANAGER -> Url"
    return True, ""


def load_test_info():
    global TEST_INFO
    with open(TEST_INFO_FILEPATH) as mfile:
        TEST_INFO = yaml.load(mfile, Loader=yaml.FullLoader)


def load_metrics_collection_info():
    global METRICS_COLLECTION_INFO
    try:
        with open(METRICS_COLLECTION_INFO_FILEPATH) as mfile:
            METRICS_COLLECTION_INFO = yaml.load(mfile, Loader=yaml.FullLoader)
    except:
        return False, "Could not load the metrics collection information"
    return True, ""