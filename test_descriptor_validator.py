
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Author: Rafael Direito (rdireito@av.it.pt)
# Date: 7th june 2021
# Last Update: 10th june 2021

# Description:
# Implementation of a validator for the testing descriptors

class Test_Descriptor_Validator:

    @staticmethod
    def is_test_description_valid(test_name, test_info, available_tests):
        # 1. check if the test contains a test_id
        test_id = test_info.get("test_id")
        if not test_id:
            return False, f"The test \"{test_name}\" doesn't contain a test_id"

        # 2. check if the testbed provides that test
        if test_id not in available_tests:
            return False, f"The test \"{test_name}\" is not supported in this tesbed"

        # 3. check if the test variables are all correctly defined
        mandatory_variables = [variable['variable_name'] for variable in available_tests[test_id]['test_variables'] if variable['mandatory']]
        test_descriptor_variables = [key for key in test_info["test_variables"].keys()]
        
        missing = []
        for mandatory_variable in mandatory_variables:
            if mandatory_variable not in test_descriptor_variables:
                missing.append(mandatory_variable)
        
        if len(missing) != 0:
            return False, f"The test {test_name} is missing the following mandatory variables: {missing}"

        return True, "" 