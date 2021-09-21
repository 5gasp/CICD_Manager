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

    def create_jenkins_pipeline_script(self, executed_tests_info, available_tests, test_instance_id):
        # base commands
        setup_environment_commands = [
            "sh 'mkdir -p ~/test_repository/\"$JOB_NAME\"'",
            "sh 'mkdir -p ~/test_results/\"$JOB_NAME\"'",
            "sh 'mkdir -p ~/test_logs/\"$JOB_NAME\"'"
        ]

        logs_commands = [
            "sh \"echo \\\"JobName: $JOB_NAME\\\" > ~/test_logs/\\\"\\\"$JOB_NAME\\\"\\\"/\\\"\\\"$JOB_NAME\\\"_${currentBuild.number}.log\\\"\"",
            "sh \"echo \\\"Current Build Number: ${currentBuild.number}\\\" >> ~/test_logs/\\\"\\\"$JOB_NAME\\\"\\\"/\\\"\\\"$JOB_NAME\\\"_${currentBuild.number}.log\\\"\"",
            "sh \"echo \\\"Log creation date: \$(date)\\\" >> ~/test_logs/\\\"\\\"$JOB_NAME\\\"\\\"/\\\"\\\"$JOB_NAME\\\"_${currentBuild.number}.log\\\"\""
        ]

        environment_obtain_tests = [
            f"ftp_user = credentials('ftp_user')",
            f"ftp_password = credentials('ftp_password')",
            f"ftp_url = '{Constants.FTP_URL}'"
        ]

        publish_results_commands = [
            """sh '''
            #!/bin/bash
            cd ~/test_results/\"$JOB_NAME\"/
            find . -type f -exec curl -u $ftp_user:$ftp_password --ftp-create-dirs -T {} ftp://$ftp_url/results/\"$JOB_NAME\"/{} \\\;
        '''""",
        ]

        cleanup_environment_commands = [
            "sh 'rm -rf ~/test_repository/\"$JOB_NAME\"'",
            "sh 'rm -rf ~/test_results/\"$JOB_NAME\"'",
            #"sh 'mkdir -p ~/test_logs/\"$JOB_NAME\"'"
        ]

        # robot tests
        tests_to_perform = {}
        variables_to_export = []
        obtain_tests_commands = []
        for test_info in executed_tests_info:
            test_id = test_info["name"]
            test_dir = available_tests[test_id]["ftp_base_location"]
            test_filename = available_tests[test_id]["test_filename"]
            # obtain test
            obtain_tests_commands.append(f"sh 'wget -r -l 0 --tries=5 -P ~/test_repository/\"$JOB_NAME\" -nH ftp://$ftp_user:$ftp_password@$ftp_url/{test_dir}'")
            # save test location. needed to run the test
            tests_to_perform[test_id] = str(os.path.join("~/test_repository/\"$JOB_NAME\"", test_dir, test_filename))
            # save env to export
            for parameter in test_info["parameters"]:
                key = f"{test_id}_{parameter['key']}"
                variables_to_export.append(f"{key} = '{parameter['value']}'")

        run_tests_commands = [
            "sh 'python3 -m pip install robotframework==4.1.1 paramiko==2.7.2'",
        ]
        for test_name, test_location  in tests_to_perform.items():
            run_tests_commands.append("sh 'python3 -m robot.run -d ~/test_results/\"$JOB_NAME\"/" + test_name +  " " + test_location +"'")


        jenkins_script_str = copy.copy(Constants.JENKINS_BASE_PIPELINE_SCRIPT)

        # update environment variables
        jenkins_script_str = self.__fill_jenkins_script("<perform_tests_environment>", variables_to_export, jenkins_script_str)
        # update setup_environment
        jenkins_script_str = self.__fill_jenkins_script("<setup_environment>", setup_environment_commands, jenkins_script_str)
        # update obtain_tests environment
        jenkins_script_str = self.__fill_jenkins_script("<obtain_tests_environment>", environment_obtain_tests, jenkins_script_str)
        # update obtain_tests
        jenkins_script_str = self.__fill_jenkins_script("<obtain_tests>", obtain_tests_commands, jenkins_script_str)
        # update perform_tests
        jenkins_script_str = self.__fill_jenkins_script("<perform_tests>", run_tests_commands, jenkins_script_str)
        # update log creation commands
        jenkins_script_str = self.__fill_jenkins_script("<logs_creation>", logs_commands, jenkins_script_str)
        # update publish_results_environment environment
        jenkins_script_str = self.__fill_jenkins_script("<publish_results_environment>", environment_obtain_tests, jenkins_script_str)        
        # update publish results commands
        jenkins_script_str = self.__fill_jenkins_script("<publish_results>", publish_results_commands, jenkins_script_str)
        # update cleanup commands
        jenkins_script_str = self.__fill_jenkins_script("<cleanup_environment>", cleanup_environment_commands, jenkins_script_str)
        # update test instance id
        jenkins_script_str = jenkins_script_str.replace("<test_id>", str(test_instance_id))
        # update CI/CD location
        jenkins_script_str = jenkins_script_str.replace("<ci_cd_manager_url_test_status_url>", Constants.CI_CD_MANAGER_URL+"/tests/test-status")
        jenkins_script_str = jenkins_script_str.replace("<ci_cd_manager_url_publish_test_results>", Constants.CI_CD_MANAGER_URL+"/tests/publish-test-results")

        config = open(Constants.BASE_PIPELINE_FILEPATH).read()
        config = config.replace("add_pipeline_configuration_here", jenkins_script_str)

        # print(repr(config))
        return config


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

    def __fill_jenkins_script(self, tag_to_replace, commands_lst, jenkins_script_str):
        item1 = re.search(tag_to_replace, jenkins_script_str, re.MULTILINE)
        item2 = re.search("{\s*" + tag_to_replace, jenkins_script_str, re.MULTILINE)
        line_offset = item1.span(0)[0] - item2.span(0)[0] - 2
        commands_str = "\n{}".format(line_offset * " ").join(commands_lst)
        return jenkins_script_str.replace(tag_to_replace, commands_str)
