#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Author: Rafael Direito (rdireito@av.it.pt)
# Date: 7th june 2021
# Last Update: 10th june 2021

# Description:
# Constains a Wrapper to interact with a Jenkins Server.

# generic imports
import jenkins
import copy
import os
import re

# custom imports
import constants as Constants


class Jenkins_Wrapper:
    
    # DECORATORS
    # Auth Decorator
    def requires_auth(func, *args, **kwargs):
        def wrapper(self, *args, **kwargs) :
            if self.jenkins_server is not None:
                return func(self, *args, **kwargs)
            else:
                print("Auth Required: To call this function you need to be authenticated in a Jenkins Server!")
        return wrapper


    # Class variables
    jenkins_server = None

    # Class main functions
    def connect_to_server(self, jenkins_connection_url, jenkins_username, jenkins_password):
        try: 
            server = jenkins.Jenkins(jenkins_connection_url, username=jenkins_username, password=jenkins_password)
            user = server.get_whoami()
        except Exception as e:
            print(f"Unable to connect to Jenkins Server. Cause:\n{str(e)}")
            return False, f"Unable to connect to Jenkins Server. Cause: {str(e)}"

        self.jenkins_server = server
        return True, ""


    @requires_auth
    def create_new_job(self, job_name, test_description, available_tests):
        job_config_xml_str = self.__create_jenkins_pipepline_script(test_description, available_tests, job_name)
        print(job_config_xml_str)
        try:
            ret = self.jenkins_server.create_job(job_name, job_config_xml_str)
        except Exception as e:
            print(f"Unable to create new job. Cause:\n{str(e)}")
            return False, f"Unable to create new job. Cause: {str(e)}" 
        return True, job_name


    @requires_auth
    def run_job(self, job_name):
        try:
            build_number = self.jenkins_server.build_job(job_name)
        except Exception as e:
            print(f"Unable to run the job '{job_name}'. Cause:\n{str(e)}")
            return False, f"Unable to run the job '{job_name}'. Cause: {str(e)}"
        return True, build_number


    def __create_jenkins_pipepline_script(self, test_description, available_tests, job_name):
        # base commands
        setup_environment_commands = [
            "sh 'rm -rf ~/test_repository'",
            "sh 'mkdir ~/test_repository'",
            "sh 'rm -rf ~/test_results'",
            "sh 'mkdir ~/test_results'",
            "sh 'mkdir -p ~/test_logs'"
        ]

        logs_commands = [
            "sh \"echo \\\"JobName: $JOB_NAME\\\" > ~/test_logs/\\\"\\\"$JOB_NAME\\\"_${currentBuild.number}.log\\\"\"",
            "sh \"echo \\\"Current Build Number: ${currentBuild.number}\\\" >> ~/test_logs/\\\"\\\"$JOB_NAME\\\"_${currentBuild.number}.log\\\"\"",
            "sh \"echo \\\"Log creation date: \$(date)\\\" >> ~/test_logs/\\\"\\\"$JOB_NAME\\\"_${currentBuild.number}.log\\\"\""
        ]

        environment_obtain_tests = [
            f"ftp_user = '{Constants.FTP_USER}'",
            f"ftp_password = '{Constants.FTP_PASSWORD}'",
            f"ftp_url = '{Constants.FTP_URL}'"
        ]

        # robot tests
        tests_to_perform = []
        variables_to_export = []
        obtain_tests_commands = []
        for test, test_info in test_description.items():
            test_id = test_info["test_id"]
            test_dir = available_tests[test_id]["ftp_base_location"]
            test_filename = available_tests[test_id]["test_filename"]
            # obtain test
            obtain_tests_commands.append(f"sh 'wget -r -l 0 --tries=5 -P ~/test_repository -nH ftp://$ftp_user:$ftp_password@$ftp_url/{test_dir}'")
            # save test location. needed to run the test
            tests_to_perform.append(os.path.join("~/test_repository", test_dir, test_filename))
            # save env to export
            for key, value in test_info["test_variables"].items():
                key = f"{test_id}_{key}"
                variables_to_export.append(f"{key} = '{value}'")

        run_tests_commands = ["sh 'python3 -m pip install robot paramiko'", "sh 'python3 -m robot.run -d ~/test_results " + " ".join(tests_to_perform)+"'"]

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


        config = open(Constants.BASE_PIPELINE_FILEPATH).read()
        config = config.replace("add_pipeline_configuration_here", jenkins_script_str)

        #print(repr(config))
        return config


    def __fill_jenkins_script(self, tag_to_replace, commands_lst, jenkins_script_str):
        item1 = re.search(tag_to_replace, jenkins_script_str, re.MULTILINE)
        item2 = re.search("{\s*" + tag_to_replace, jenkins_script_str, re.MULTILINE)
        line_offset = item1.span(0)[0] - item2.span(0)[0] - 2
        commands_str = "\n{}".format(line_offset * " ").join(commands_lst)
        return jenkins_script_str.replace(tag_to_replace, commands_str)