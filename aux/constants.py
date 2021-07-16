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
            environment {
                comm_token = credentials('communication_token')
                test_id = <test_id>
            }
            steps {
                <setup_environment>
            }
            post {
                failure {
                    sh 'curl --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'", "success":false, "state": "ENVIRONMENT_SETUP_CI_CD_AGENT"}\\' <ci_cd_manager_url_test_status_url>'
                }
                success {
                    sh 'curl --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'", "success":true, "state": "ENVIRONMENT_SETUP_CI_CD_AGENT"}\\'  <ci_cd_manager_url_test_status_url>'
                }
            }
        }
        stage('Obtain Tests') {
            environment {
                <obtain_tests_environment>
                comm_token = credentials('communication_token')
                test_id = <test_id>
            }
            steps {
                <obtain_tests>
            }
            post {
                failure {
                    sh 'curl --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'", "success":false, "state": "OBTAINED_TESTS_ON_CI_CD_AGENT"}\\' <ci_cd_manager_url_test_status_url>'
                }
                success {
                    sh 'curl --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'", "success":true, "state": "OBTAINED_TESTS_ON_CI_CD_AGENT"}\\'  <ci_cd_manager_url_test_status_url>'
                }
            }
        }
        stage('Perform Tests') {
            environment {
                <perform_tests_environment>
                comm_token = credentials('communication_token')
                test_id = <test_id>
            }
            steps {
                <perform_tests>
            }
            post {
                failure {
                    sh 'curl --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'", "success":false, "state": "PERFORMED_TESTS_ON_CI_CD_AGENT"}\\' <ci_cd_manager_url_test_status_url>'
                }
                success {
                    sh 'curl --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'", "success":true, "state": "PERFORMED_TESTS_ON_CI_CD_AGENT"}\\'  <ci_cd_manager_url_test_status_url>'
                }
            }
        }
        stage('Logs') {
            environment {
                comm_token = credentials('communication_token')
                test_id = <test_id>
            }
            steps {
                <logs_creation>
            }
            post {
                failure {
                    sh 'curl --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'", "success":false, "state": "CREATED_LOGS_ON_CI_CD_AGENT"}\\' <ci_cd_manager_url_test_status_url>'
                }
                success {
                    sh 'curl --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'", "success":true, "state": "CREATED_LOGS_ON_CI_CD_AGENT"}\\'  <ci_cd_manager_url_test_status_url>'
                }
            }
        }
        stage('Publish Results') {
            environment {
                <publish_results_environment>
                comm_token = credentials('communication_token')
                test_id = <test_id>
            }
            steps {
                <publish_results>
            }
            post {
                failure {
                    sh 'curl --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'", "success":false, "state": "PUBLISHED_TEST_RESULTS"}\\' <ci_cd_manager_url_test_status_url>'
                }
                success {
                    sh 'curl --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'", "success":true, "state": "PUBLISHED_TEST_RESULTS"}\\'  <ci_cd_manager_url_test_status_url>'
                }
            }
        }
        stage('Cleanup environment') {
            environment {
                comm_token = credentials('communication_token')
                test_id = <test_id>
            }
            steps {
                <cleanup_environment>
            }
            post {
                failure {
                    sh 'curl --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'", "success":false, "state": "CLEANED_TEST_ENVIRONMENT"}\\' <ci_cd_manager_url_test_status_url>'
                }
                success {
                    sh 'curl --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'", "success":true, "state": "CLEANED_TEST_ENVIRONMENT"}\\'  <ci_cd_manager_url_test_status_url>'
                }
            }
        }
    }
}"""

TEST_STATUS ={
    "submitted_on_manager": "SUBMITTED_TO_CI_CD_MANAGER",
    "ci_cd_agent_provisioned": "PROVISIONED_CI_CD_AGENT",
    "ci_cd_agent_auth": "AUTHENTICATED_ON_CI_CD_AGENT",
    "created_comm_token": "CREATED_COMMUNICATION_TOKEN_BETWEEN_MANAGER_AND_AGENT",
    "created_pipeline_script": "CREATED_PIPELINE_SCRIPT",
    "submitted_pipeline_script": "SUBMITTED_PIPELINE_SCRIPT",
    "ci_cd_agent_setup_environment": "ENVIRONMENT_SETUP_CI_CD_AGENT",
    "ci_cd_agent_obtained_tests": "OBTAINED_TESTS_ON_CI_CD_AGENT",
    "ci_cd_agent_performed_tests": "PERFORMED_TESTS_ON_CI_CD_AGENT",
    "ci_cd_agent_created_logs": "CREATED_LOGS_ON_CI_CD_AGENT",
    "ci_cd_agent_published_test_results": "PUBLISHED_TEST_RESULTS",
    "ci_cd_agent_cleaned_test_environment": "CLEANED_TEST_ENVIRONMENT",
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