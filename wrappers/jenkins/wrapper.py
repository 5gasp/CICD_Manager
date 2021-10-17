#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Author: Rafael Direito (rdireito@av.it.pt)
# Date: 7th june 2021
# Last Update: 10th june 2021

# Description:
# Constains a Wrapper to interact with a Jenkins Server.

# generic imports
from requests.auth import HTTPBasicAuth
import requests
import logging
import jenkins
import inspect
import json
import copy
import sys
import os
import re

# import from parent directory
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

# custom imports
import aux.constants as Constants
import wrappers.jenkins.constants as JenkinsConstants
import wrappers.jenkins.pipeline_configuration as JenkinsPipelineConfiguration

# Logger
logging.basicConfig(
    format="%(module)-15s:%(levelname)-10s| %(message)s",
    level=logging.INFO
)

class Jenkins_Wrapper:

    # DECORATORS
    # Auth Decorator
    def requires_auth(func, *args, **kwargs):
        def wrapper(self, *args, **kwargs):
            if self.jenkins_server is not None:
                return func(self, *args, **kwargs)
            else:
                logging.error("Auth Required: To call this function you need to be authenticated in a Jenkins Server!")
        return wrapper

    # Class variables
    jenkins_server = None
    jenkins_username = None
    jenkins_password = None
    jenkins_connection_url = None

    # Class main functions
    def connect_to_server(self, jenkins_connection_url, jenkins_username, jenkins_password):
        self.jenkins_connection_url = jenkins_connection_url
        self.jenkins_username = jenkins_username
        self.jenkins_password = jenkins_password
        try:
            server = jenkins.Jenkins(jenkins_connection_url, username=jenkins_username, password=jenkins_password)
            user = server.get_whoami()
        except Exception as e:
            return False, f"Unable to connect to Jenkins Server. Cause: {str(e)}"

        self.jenkins_server = server
        return True, ""


    @requires_auth
    def get_build_log(self, job_name, build_number):
        try:
            ret = self.jenkins_server.get_build_console_output(job_name, build_number)
        except Exception as e:
            return False, f"Unable to get build logs. Cause: {str(e)}"
        return True, ret


    @requires_auth
    def get_last_build_number(self, job_name):
        try:
            ret = self.jenkins_server.get_job_info(job_name)["nextBuildNumber"]
        except Exception as e:
            return False, f"Unable to get last build number for job {job_name}. Cause: {str(e)}"
        return True, ret


    @requires_auth
    def create_new_job(self, job_name, job_config_xml_str):
        try:
            ret = self.jenkins_server.create_job(job_name, job_config_xml_str)
        except Exception as e:
            return False, f"Unable to create new job. Cause: {str(e)}"
        return True, job_name


    @requires_auth
    def run_job(self, job_name):
        try:
            build_number = self.jenkins_server.build_job(job_name)
        except Exception as e:
            return False, f"Unable to run the job '{job_name}'. Cause: {str(e)}"
        return True, build_number


    @requires_auth
    def create_credential(self, credential_name, credential_value, credential_description="", credential_scope="GLOBAL"):
        # create session
        s = requests.Session()

        # 1. get a valid crumb
        try:
            r = s.get(f'{self.jenkins_connection_url}/crumbIssuer/api/json',
                      auth=HTTPBasicAuth(self.jenkins_username, self.jenkins_password),
                      timeout=10)

            if r.status_code != 200:
                raise Exception(r.content)

            crumb = json.loads(r.text)['crumb']
        except Exception as e:
            return False, f"Unable to get Jenkins Crumb. Cause:\n{str(e)}"

        # 2. using the received crumb, get the an auth token
        try:
            token_name = "communicationToken"
            r = s.post(f'{self.jenkins_connection_url}/me/descriptorByName/jenkins.security.ApiTokenProperty/generateNewToken?newTokenName={token_name}',
                       auth=HTTPBasicAuth(self.jenkins_username, self.jenkins_password),
                       headers={'Jenkins-Crumb': crumb},
                       timeout=10)

            if r.status_code != 200:
                raise Exception(r.content)

            token_name = json.loads(r.text)['data']['tokenName']
            token_value = json.loads(r.text)['data']['tokenValue']
        except Exception as e:
            return False, f"Unable to get Jenkins Auth Token. Cause:\n{str(e)}"

        # 3. remove previous credential, if it exists
        try:
            r = s.post(f'{self.jenkins_connection_url}/credentials/store/system/domain/_/credential/{credential_name}/doDelete',
                       auth=HTTPBasicAuth(self.jenkins_username, token_value),
                       headers={'Jenkins-Crumb': crumb},
                       timeout=10)

            if r.status_code != 200 and r.status_code != 404:
                raise Exception(r.content)
        except Exception as e:
            return False, f"Unable to remove Jenkins credential. Cause:\n{str(e)}"

        # 4. create a credential
        try:
            # data to be submitted
            json_data = {
                "": "0",
                "credentials": {
                    "scope": credential_scope,
                    "id": credential_name,
                    "secret": credential_value,
                    "description": credential_description,
                    "$class": "org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl"
                }
            }

            # generate encoded url
            encoded_url = requests.Request(
                "POST",
                f'{self.jenkins_connection_url}/credentials/store/system/domain/_/createCredentials',
                params={"json": json.dumps(json_data)}
            ).prepare().url

            # submit new credential
            r = s.post(encoded_url,
                       auth=HTTPBasicAuth( self.jenkins_username, token_value),
                       headers={'Content-Type': 'application/x-www-form-urlencoded'},
                       timeout=10)

            if r.status_code != 200:
                raise Exception(r.content)
        except Exception as e:
            return False, f"Unable to create Jenkins Credential. Cause:\n{str(e)}"
        
        return True, ""


    def create_jenkins_pipeline_script(self, executed_tests_info, available_tests, descriptor_metrics_collection, metrics_collection_information, test_instance_id):
        jenkins_script_str = copy.copy(JenkinsConstants.JENKINS_BASE_PIPELINE_SCRIPT)
        pipeline_configuration = JenkinsPipelineConfiguration.Jenkins_Pipeline_Configuration(jenkins_script_str, executed_tests_info, available_tests, descriptor_metrics_collection, metrics_collection_information, test_instance_id)
        conf = pipeline_configuration.create_jenkins_pipeline_script()
        return conf
  