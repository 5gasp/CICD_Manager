# -*- coding: utf-8 -*-
# @Author: Rafael Direito
# @Date:   22-05-2022 10:25:05
# @Email:  rdireito@av.it.pt
# @Last Modified by:   Rafael Direito
# @Last Modified time: 09-06-2022 16:52:33
# @Description: 

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Author: Rafael Direito (rdireito@av.it.pt)
# Date: 7th june 2021
# Last Update: 10th june 2021

# Description:
# Implementation of a validator for the testing descriptors

import sys
import os
import inspect
from cerberus import Validator
from sql_app import crud

# import from parent directory
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

# custom imports
import testing_descriptors_validator.schema as schema
import aux.constants as Constants
import aux.utils as Utils


class Test_Descriptor_Validator:

    def __init__(self, descriptor_content):
        self.descriptor_content = descriptor_content
        self.executed_tests_info = None


    def is_test_description_valid(test_name, test_info, available_tests):
        # 1. check if the test contains a test_id
        test_id = test_info.get("test_id")
        if not test_id:
            return False, f"The test \"{test_name}\" doesn't contain a test_id"
        # 2. check if the testbed provides that test
        if test_id not in available_tests:
            return False, f"The test \"{test_name}\" is not supported in this testbed"

        # 3. check if the test variables are all correctly defined
        mandatory_variables = [variable['variable_name'] for variable in available_tests[test_id]['test_variables'] if variable['mandatory']]
        test_descriptor_variables = [key for key in test_info["test_variables"].keys()]
        
        missing = [mandatory_variable for mandatory_variable in mandatory_variables  if mandatory_variable not in test_descriptor_variables]
        
        if len(missing) != 0:
            return False, f"The test {test_name} is missing the following mandatory variables: {missing}"

        return True, "" 


 
    def validate_tests_parameters(self, testbed_tests):
        errors = []
        try:
            executed_tests_info = []
            executed_tests_descriptor_id = []
            for execution in self.descriptor_content["test_phases"]["execution"]:
                for executions in execution["executions"]:
                    executed_tests_descriptor_id +=  executions["testcase_ids"]
            for test_case in self.descriptor_content["test_phases"]["setup"]["testcases"]:
                if test_case["testcase_id"] in executed_tests_descriptor_id:
                    executed_tests_info.append(test_case)     
        except Exception as e:
            errors.append(e)
        
        self.executed_tests_info = executed_tests_info 
        
        if len(errors) == 0:
            for test_info in executed_tests_info[0:1]:
                td_test_defined_parameters = {parameter["key"]: parameter["value"] for parameter in test_info["parameters"]}
                # check if test exists
                has_test = False
                # Hotfix
                if test_info["type"] != "predefined":
                    has_test = True
                    continue
                # End of hotfix
                for testbed_test in testbed_tests:
                    if test_info["name"] == testbed_test.name:
                        has_test = True
                    
                        for test_variable in testbed_test.testinfo_variables:
                            # check if all the test mandatory parameters are defined in the descriptor
                            if test_variable.variable_name in td_test_defined_parameters or not test_variable.mandatory:
                                # check if the value respects its possible options (if that's the case)
                                options = [option.name for option in test_variable.possible_options]
                                if len(test_variable.possible_options) != 0 and td_test_defined_parameters[test_variable.variable_name] not in options:
                                    errors.append(f"The parameter \"{test_variable.variable_name}\", for the test {test_info['name']}, is not according to its possible_options.")
                            else:
                                errors.append(f"The parameter \"{test_variable.variable_name}\" must be defined for the test {test_info['name']}.")
                    elif test_info["type"] == "developer-defined":
                        has_test = True
                        
                if not has_test:
                    errors.append(f"{test_info['name']} doesn't exist in the chosen testbed.")
                # if test_info["name"] in testbed_tests:
                #     for test_variable in testbed_tests[test_info["name"]]["test_variables"]:
                #         # check if all the test mandatory parameters are defined in the descriptor
                #         if test_variable["variable_name"] in td_test_defined_parameters or not test_variable["mandatory"]:
                #             # check if the value respects its possible options (if that's the case)
                #             if len(test_variable["possible_options"]) != 0 and td_test_defined_parameters[test_variable["variable_name"]] not in test_variable["possible_options"]:
                #                 errors.append(f"The parameter \"{test_variable['variable_name']}\", for the test {test_info['name']}, is not according to its possible_options.")
                #         else:
                #             errors.append(f"The parameter \"{test_variable['variable_name']}\" must be defined for the test {test_info['name']}.")
                # else:
                #     errors.append(f"{test_info['name']} doesn't exist in the chosen testbed.")
    
        return errors


    def validate_metrics_collection_process(self, metrics_collection_information):
        mandatory_parameters = [mci["variable_name"] for mci in metrics_collection_information["metrics_collection"]["variables"] if mci["mandatory"]]
        if 'metrics_collection' in self.descriptor_content["test_phases"]["setup"]:
            descriptors_metrics_collection_processes = self.descriptor_content["test_phases"]["setup"]["metrics_collection"]
            for descriptors_metrics_collection_process in descriptors_metrics_collection_processes:
                # get the defined paraemeters
                described_keys = [ param["key"] for param in descriptors_metrics_collection_process["parameters"]]
                # check if all the mandatory parameters are defined
                all_mandatory_tags_defined = all(elem in described_keys for elem in mandatory_parameters)
                if not all_mandatory_tags_defined:
                    return False
        return True
    

    def validate_structure(self):
        validator = Validator()
        validator.validate(self.descriptor_content, schema.VALIDATION_SCHEMA)
        return validator.errors
