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

# Logger
logging.basicConfig(
    format="%(module)-15s:%(levelname)-10s| %(message)s",
    level=logging.INFO
)

class Jenkins_Pipeline_Configuration:
    
    def __init__(self, jenkins_script_str, executed_tests_info, available_tests, descriptor_metrics_collection, metrics_collection_information,  test_instance_id):
        self.jenkins_script_str = jenkins_script_str
        self.executed_tests_info = executed_tests_info
        self.available_tests = available_tests
        self.descriptor_metrics_collection = descriptor_metrics_collection
        self.metrics_collection_information = metrics_collection_information
        self.test_instance_id = test_instance_id


    def create_jenkins_pipeline_script(self):
    
        # fill the pipeline script
        self.add_environment_setup_to_jenkins_pipeline_script()
        self.add_obtain_metrics_collection_files_to_jenkins_pipeline_script(self.descriptor_metrics_collection, self.metrics_collection_information)
        self.add_metrics_colllection_mechanism_to_jenkins_pipeline_script(self.descriptor_metrics_collection, self.metrics_collection_information)
        self.add_obtain_and_perform_tests_to_jenkins_pipeline_script(self.executed_tests_info, self.available_tests)
        self.add_publish_results_to_jenkins_pipeline_script()
        self.add_cleanup_environment_commands_to_jenkins_pipeline_script()

        # update test instance id
        self.jenkins_script_str = self.jenkins_script_str.replace("<test_id>", str(self.test_instance_id))
        # update CI/CD location
        self.jenkins_script_str = self.jenkins_script_str.replace("<ci_cd_manager_url_test_status_url>", Constants.CI_CD_MANAGER_URL+"/tests/test-status")
        self.jenkins_script_str = self.jenkins_script_str.replace("<ci_cd_manager_url_publish_test_results>", Constants.CI_CD_MANAGER_URL+"/tests/publish-test-results")

        config = JenkinsConstants.BASE_PIPELINE
        config = config.replace("add_pipeline_configuration_here", self.jenkins_script_str)

        return config
  


    def add_environment_setup_to_jenkins_pipeline_script(self):
        setup_environment_commands = [
            "sh 'mkdir -p ~/test_repository/\"$JOB_NAME\"'",
            "sh 'mkdir -p ~/test_results/\"$JOB_NAME\"'",
            "sh 'mkdir -p ~/test_logs/\"$JOB_NAME\"'"
        ]
        return self.__update_jenkins_script("<setup_environment>", setup_environment_commands)


    def add_obtain_and_perform_tests_to_jenkins_pipeline_script(self, executed_tests_info, available_tests):
        needed_python_modules =[
            "robotframework==4.1.1",
            "paramiko==2.7.2",
            "python3-nmap==1.5.1",
        ]

        environment_obtain_tests = [
            f"ftp_user = credentials('ftp_user')",
            f"ftp_password = credentials('ftp_password')",
            f"ftp_url = '{Constants.FTP_URL}'"
        ]

        run_tests_commands = []
        obtain_tests_commands = set()

        # add needed python modules
        run_tests_commands.append(f"sh 'python3 -m pip install {' '.join(needed_python_modules)}'")

        # robot tests
        tests_to_perform = {}        
        print("---", executed_tests_info)
        for test_info in executed_tests_info:
            test_id = test_info["name"]
            print("test_id--", test_id)
            test_dir = available_tests[test_id]["ftp_base_location"]
            test_filename = available_tests[test_id]["test_filename"]
            # obtain test
            obtain_tests_commands.add(f"sh 'wget -r -l 0 --tries=5 -P ~/test_repository/\"$JOB_NAME\" -nH ftp://$ftp_user:$ftp_password@$ftp_url/{test_dir}'")
            # save test location. needed to run the test
            tests_to_perform[test_id] = str(os.path.join("~/test_repository/\"$JOB_NAME\"", test_dir, test_filename))
            # save env to export
            export_variables_commands = []
            for parameter in test_info["parameters"]:
                key = f"{test_id}_{parameter['key']}"
                value = parameter['value']
                export_variables_commands.append(f"export {key}={value}")
                
            export_variables_commands_str = " ; ".join(export_variables_commands)
            run_tests_commands.append(f"sh '{ export_variables_commands_str} ; python3 -m robot.run -d ~/test_results/\"$JOB_NAME\"/{test_id}-test-id-{test_info['testcase_id']} {tests_to_perform[test_id]}'")
        # fill jenkins pipeline script
        self.__update_jenkins_script("<obtain_tests_environment>", environment_obtain_tests)
        self.__update_jenkins_script("<obtain_tests>", obtain_tests_commands)
        self.__update_jenkins_script("<perform_tests>", run_tests_commands)
        

    def add_publish_results_to_jenkins_pipeline_script(self):
        publish_results_environment = [
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
        self.__update_jenkins_script("<publish_results>", publish_results_commands)
        self.__update_jenkins_script("<publish_results_environment>", publish_results_environment)  

    
    def add_cleanup_environment_commands_to_jenkins_pipeline_script(self):
        cleanup_environment_commands = [
            "sh 'rm -rf ~/test_repository/\"$JOB_NAME\"'",
            "sh 'rm -rf ~/test_results/\"$JOB_NAME\"'",
        ]

        return self.__update_jenkins_script("<cleanup_environment>", cleanup_environment_commands)


    def add_obtain_metrics_collection_files_to_jenkins_pipeline_script(self, descriptor_metrics_collection, metrics_collection_information):
        print(descriptor_metrics_collection)
        print(metrics_collection_information)

        obtain_metrics_environment = [
            f"ftp_user = credentials('ftp_user')",
            f"ftp_password = credentials('ftp_password')",
            f"ftp_url = '{Constants.FTP_URL}'"
        ]

        obtain_metrics_collection_file_commands = []
        metrics_dir = metrics_collection_information["metrics_collection"]["ftp_base_location"]
        obtain_metrics_collection_file_commands.append(f"sh 'wget -r -l 0 --tries=5 -P ~/test_repository/\"$JOB_NAME\" -nH ftp://$ftp_user:$ftp_password@$ftp_url/{metrics_dir}'")
        self.__update_jenkins_script("<obtain_metrics_collection_files>", obtain_metrics_collection_file_commands)
        self.__update_jenkins_script("<obtain_metrics_environment>", obtain_metrics_environment)


    def add_metrics_colllection_mechanism_to_jenkins_pipeline_script(self, descriptor_metrics_collection, metrics_collection_information):
        needed_python_modules =[
            "scp==0.14.1",
        ]
        execute_metrics_collection_commands = []
        execute_metrics_collection_commands.append(f"sh 'python3 -m pip install {' '.join(needed_python_modules)}'")
        # robot tests
        metrics_to_collect = {}        
        for metrics_collection in descriptor_metrics_collection:
            metrics_collection_id = "metrics_collection"
            metrics_dir = metrics_collection_information["metrics_collection"]["ftp_base_location"]
            metrics_filename = metrics_collection_information["metrics_collection"]["test_filename"]
            # save test location. needed to run the test
            metrics_to_collect[metrics_collection_id] = str(os.path.join("~/test_repository/\"$JOB_NAME\"", metrics_dir, metrics_filename))
            # save env to export
            export_variables_commands = []
            for parameter in metrics_collection["parameters"]:
                key = f"{metrics_collection_id}_{parameter['key']}"
                value = parameter['value']
                export_variables_commands.append(f"export {key}={value}")
            export_variables_commands.append("export metrics_collection_action=<action>")

            export_variables_commands_str = " ; ".join(export_variables_commands)
            execute_metrics_collection_commands.append(f"sh '{ export_variables_commands_str} ; python3 -m robot.run -d ~/test_results/\"$JOB_NAME\"/{metrics_collection_id} {metrics_to_collect[metrics_collection_id]}'")
        
        
        self.__update_jenkins_script("<start_metrics_collection>", execute_metrics_collection_commands)
        self.jenkins_script_str = self.jenkins_script_str.replace("<action>", "start")
        self.__update_jenkins_script("<end_metrics_collection>", execute_metrics_collection_commands)
        self.jenkins_script_str = self.jenkins_script_str.replace("<action>", "stop")
        

    def __update_jenkins_script(self, tag_to_replace, commands_lst):
        item1 = re.search(tag_to_replace, self.jenkins_script_str, re.MULTILINE)
        item2 = re.search("{\s*" + tag_to_replace, self.jenkins_script_str, re.MULTILINE)
        line_offset = item1.span(0)[0] - item2.span(0)[0] - 2
        commands_str = "\n{}".format(line_offset * " ").join(commands_lst)
        self.jenkins_script_str = self.jenkins_script_str.replace(tag_to_replace, commands_str)