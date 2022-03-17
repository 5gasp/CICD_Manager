
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
from datetime import datetime
from fastapi.responses import JSONResponse
import logging
import yaml
import requests
from sqlalchemy.orm import class_mapper

# custom imports
import aux.constants as Constants
from sql_app import crud
import sql_app.schemas.ci_cd_manager as Schemas 

# Logger
logging.basicConfig(
    format="%(module)-15s:%(levelname)-10s| %(message)s",
    level=logging.INFO
)

def create_response(status_code=200, data=[], errors=[], success=True, message=""):
    return JSONResponse(status_code=status_code, content={"message": message, "success": success, 
    "data": data, "errors": errors}, headers={"Access-Control-Allow-Origin": "*"})


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
                # if testbed has not been created yet
                if not crud.get_testbed_by_id(session, t_id):
                    ltrdata = Schemas.LTRData_Base(
                        location=testbed_data['ltr']['location'],
                        user=testbed_data['ltr']['user'],
                        password=testbed_data['ltr']['password']
                    )
                    testbed_payload = Schemas.Testbed_Create(name=t_name,
                    description=t_description,id=t_id, ltrdata=ltrdata)

                    crud.create_testbed(session,testbed_payload)
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
        if len(set(tests_data.keys())) != len(tests_data.keys()):
            return False, "Duplicated testbeds"

        for testbed in tests_data:
            if crud.get_testbed_by_id(db, testbed) is None:
                return False, "Testbed doesn't exist"

    return True, ""    


def load_testbeds_info(testbed_info_file):
    try:
        with open(testbed_info_file) as mfile:
            testbeds_data = yaml.load(mfile, Loader=yaml.FullLoader)
            Constants.TESTBEDS_INFO = testbeds_data
        return True, ""   
    except:
        return False, "Unable to load testbeds information"


def get_ltr_info_for_testbed(testbed_id):
    ltr_info = Constants.TESTBEDS_INFO["testbeds"][testbed_id]["ltr"]
    return ltr_info


# TODO: Create a class with a decorator for NODS Authentication
def get_nods_token():
    auth_url = f'{Constants.NODS_HOST}/auth/realms/openslice/protocol/openid-connect/token'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data={'username': Constants.NODS_USER, 'password': Constants.NODS_PASSWORD,
     'grant_type':'password', 'client_id':'osapiWebClientId','client_secret':'secret'}
    logging.info("Authenticating to Nods")
    response = requests.post(url=auth_url, headers=headers, data=data)
    token = response.json()['access_token']
    logging.info("Retrieved NODS Auth Token")
    return True, token


def get_serviceTestSpecification(token,_id):
    auth_url = f'{Constants.NODS_HOST}/tmf-api/serviceTestManagement/v4/serviceTestSpecification/{_id}'
    headers = {'Authorization': f'Bearer {token}'}
    try:
        response = requests.get(url=auth_url,headers=headers)
        if response.status_code != 200:
            raise Exception(response.content)
    except Exception as e:
        return False, f"Unable to get ServiceTestSpecification. Reason: {e}"
    return True, response.json()

def get_serviceTestDescriptor(token,url):
    headers = {'Authorization': f'Bearer ' + token}
    url =  f'{Constants.NODS_HOST}/tmf-api{url}'
    response = requests.get(url=url,headers=headers)
    try:
        if response.status_code != 200:
            raise Exception(response.content)
    except Exception as e:
        return False, f"Unable to get ServiceTest Descriptor. Reason: {e}"
    return True,response

def patch_results(token,nods_id,data):
    headers = {'Authorization': f'Bearer ' + token,'Content-Type': 'application/json'}
    logging.info("patching data result on NODS")
    url =  f'{Constants.NODS_HOST}/tmf-api/serviceTestManagement/v4/serviceTest/{nods_id}'
    response = requests.patch(url=url,headers=headers,json=data)
    print(response.text)
    return True,response


###https://stackoverflow.com/questions/23554119/convert-sqlalchemy-orm-result-to-dict
def object_to_dict(obj, found=None):
    if found is None:
        found = set()
    mapper = class_mapper(obj.__class__)
    columns = [column.key for column in mapper.columns]
    get_key_value = lambda c: (c, getattr(obj, c).isoformat()) if isinstance(getattr(obj, c), datetime) else (c, getattr(obj, c))
    out = dict(map(get_key_value, columns))
    for name, relation in mapper.relationships.items():
        if relation not in found:
            found.add(relation)
            related_obj = getattr(obj, name)
            if related_obj is not None:
                if relation.uselist:
                    out[name] = [object_to_dict(child, found) for child in related_obj]
                else:
                    out[name] = object_to_dict(related_obj, found)
    return out