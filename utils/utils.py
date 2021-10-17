
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Author: Rafael Direito (rdireito@av.it.pt)
# Date: 7th june 2021
# Last Update: 12th july 2021

# Description:
# Defines functions that simplify some processes
# This module is being used in allmost all the other modules


# generic imports
from fastapi.responses import JSONResponse
import logging
import yaml

# custom imports
import aux.constants as Constants
from sql_app import crud

# Logger
logging.basicConfig(
    format="%(module)-15s:%(levelname)-10s| %(message)s",
    level=logging.INFO
)

def create_response(status_code=200, data=[], errors=[], success=True, message=""):
    return JSONResponse(status_code=status_code, content={"message": message, "success": success, "data": data, "errors": errors}, headers={"Access-Control-Allow-Origin": "*"})


def load_testbeds_to_db(session, testbed_info_file):
    with open(testbed_info_file) as mfile:
        testbeds_data = yaml.load(mfile, Loader=yaml.FullLoader)

        if "testbeds" not in testbeds_data.keys():
            return False, "Wrong structure"

        testbeds_data = testbeds_data["testbeds"]

        if len(set(testbeds_data.keys())) != len(testbeds_data.keys()):
            return False, "Duplicated keys"

        try:
            for testbed, testbed_data in testbeds_data.items():
                t_id = testbed
                t_name = testbed_data["name"]
                t_description = testbed_data["description"]
                # if testbed has not been crated yet
                if not crud.get_testbed_by_id(session, t_id):
                    crud.create_testbed(session, t_id, t_name, t_description)
        except Exception as e:
            return False, "Wrong structure: " + str(e)
        
    return True, ""


def load_test_info(db, tests_info_file):
    with open(tests_info_file) as mfile:
        tests_data = yaml.load(mfile, Loader=yaml.FullLoader)
        Constants.TEST_INFO = tests_data

        if "tests" not in tests_data.keys():
            return False, "Wrong structure"

        tests_data = tests_data["tests"]
        print(tests_data.keys())
        if len(set(tests_data.keys())) != len(tests_data.keys()):
            return False, "Duplicated testbeds"

        for testbed in tests_data:
            if crud.get_testbed_by_id(db, testbed) is None:
                return False, "Testbed doesn't exist"

        # ... further elaborate, once we have the final testing descriptors

    return True, ""    