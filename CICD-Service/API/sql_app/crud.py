# -*- coding: utf-8 -*-
# @Author: Rafael Direito
# @Date:   22-05-2022 10:25:05
# @Email:  rdireito@av.it.pt
# @Last Modified by:   Rafael Direito
# @Last Modified time: 26-05-2022 14:44:00
# @Description: Contains all the CRUD operations over the Database


import logging
import random
from statistics import mode
import string
# generic imports
from os import access, name
from collections import Counter
from sqlalchemy.orm import Session, joinedload
import yaml 

# custom imports
from . import models
from sql_app.schemas import ci_cd_manager as ci_cd_manager_schemas, test_info as testinfo_schemas
from aux import auth
from sql_app.CRUD import agents as agents_crud
from exceptions.auth import *
from exceptions.agents import *
from aux import constants as Constants

# Logger
logging.basicConfig(
    format="%(module)-15s:%(levelname)-10s| %(message)s",
    level=logging.INFO
)

# ---------------------------------------- #
# ---------------- Metrics --------------- #
# ---------------------------------------- #
def create_metrics_dasboard(db: Session, test_id, url, username, password):
    metrics_dashboard_instance = models.Test_Metrics_Dashboard(
        test_id=test_id,
        url=url,
        access_username=username,
        access_password=password
    )
    db.add(metrics_dashboard_instance)
    db.commit()
    db.refresh(metrics_dashboard_instance)
    logging.info(
        f"Created metrics dashboard with id {metrics_dashboard_instance.id}"
    )
    return metrics_dashboard_instance

def get_metrics_dasboard(db: Session, test_id: int):
    metrics_dashboard_instance = db.query(models.Test_Metrics_Dashboard)\
        .filter(models.Test_Metrics_Dashboard.test_id == test_id)
    return metrics_dashboard_instance

# ---------------------------------------- #
# ----------------- Logs ----------------- #
# ---------------------------------------- #
def create_logs_dasboard(db: Session, test_id, url, username, password):
    logs_dashboard_instance = models.Test_Logs_Dashboard(
        test_id=test_id,
        url=url,
        access_username=username,
        access_password=password
    )
    db.add(logs_dashboard_instance)
    db.commit()
    db.refresh(logs_dashboard_instance)
    logging.info(
        f"Created logs dashboard with id {logs_dashboard_instance.id}"
    )
    return logs_dashboard_instance

def get_logs_dasboard(db: Session, test_id: int):
    logs_dashboard_instance = db.query(models.Test_Logs_Dashboard)\
        .filter(models.Test_Logs_Dashboard.test_id == test_id)
    return logs_dashboard_instance

# ---------------------------------------- #
# --------------- Testbeds --------------- #
# ---------------------------------------- #

def create_testbed(db: Session, testbed: ci_cd_manager_schemas.Testbed_Base):
    testbed_instance = models.Testbed(name=testbed.name, description=testbed.description)
    db.add(testbed_instance)
    db.commit()
    db.refresh(testbed_instance)
    logging.info(f"Created testbed with id {testbed_instance.id}")
    return testbed_instance

def create_testbed(db: Session, testbed_id: int, testbed_name: str, testbed_description: str):
    testbed_instance = models.Testbed(id=testbed_id, name=testbed_name, description=testbed_description)
    db.add(testbed_instance)
    db.commit()
    db.refresh(testbed_instance)
    logging.info(f"Created testbed with id {testbed_instance.id}")
    return testbed_instance


def create_testbed(db: Session, testbed: ci_cd_manager_schemas.Testbed_Create):
    testbed_instance = models.Testbed(
    id=testbed.id,
    name=testbed.name,
    description=testbed.description
    )
    db.add(testbed_instance)
    db.commit()
    db.refresh(testbed_instance)
    logging.info(f"Created testbed with id {testbed_instance.id}")
    return testbed_instance

def get_testbed_by_id(db: Session, id: str):
    return db.query(models.Testbed).filter(models.Testbed.id == id).first()


def get_testbed_by_name(db: Session, testbed_name: str):
    return db.query(models.Testbed).filter(models.Testbed.name == testbed_name).first()


def get_all_testbeds(db: Session, skip: int = 0, limit: int = 500):
    return db.query(models.Testbed).offset(skip).limit(limit).all()

# ---------------------------------------- #
# ------------- Test Stages -------------- #
# ---------------------------------------- #

def create_test_stage(
        db: Session, 
        test_instance_id: int,
        testing_agent_id: int,
        jenkins_pipeline: str = None
    ):
    test_stage = models.Test_Instance_Stage(
        test_instance_id=test_instance_id,
        testing_agent_id=testing_agent_id,
        jenkins_pipeline=jenkins_pipeline
    )
    db.add(test_stage)
    db.commit()
    db.refresh(test_stage)

    create_test_stage_status(
        db=db,
        test_stage_id=test_stage.id,
        state=models.TestStageStatus.INIT,
    )

    logging.info(f"Created test stage for test instance '{test_instance_id}'.")
    return test_stage

def update_test_stage_with_jenkins_pipeline(
        db: Session, 
        test_stage_id: int,
        jenkins_pipeline: str
    ):

    db_test_stage = db.query(models.Test_Instance_Stage)\
        .filter(models.Test_Instance_Stage.id == test_stage_id).first()
    
    db_test_stage.jenkins_pipeline = jenkins_pipeline
    db.commit()
    db.refresh(db_test_stage)

    create_test_stage_status(
        db=db,
        test_stage_id=db_test_stage.id,
        state=models.TestStageStatus.CREATED_PIPELINE_SCRIPT,
    )
    logging.info(f"Updated test_stage with id {db_test_stage.id}.")
    return db_test_stage

def create_test_stage_status(
    db: Session, 
    test_stage_id: int,
    state: models.TestStageStatus
):
    test_stage_status = models.Test_Instance_Stage_Status(
        test_stage_id=test_stage_id,
        state=state
    )
    db.add(test_stage_status)
    db.commit()
    db.refresh(test_stage_status)

    logging.info(
        f"Created test stage status for test stage '{test_stage_id}': {state}."
    )
    return test_stage_status

def get_test_stages_with_status_for_test_instance(
    db: Session, 
    test_instance_id: int,
):
    db_test_stages = db.query(models.Test_Instance_Stage)\
        .filter(models.Test_Instance_Stage.test_instance_id == test_instance_id)\
        .all()
    
    return {
        db_test_stage: get_test_stage_statuses(db, db_test_stage.id)
        for db_test_stage
        in db_test_stages
    }

def get_test_stage(
    db: Session, 
    test_stage_id: int,
):
    return db.query(models.Test_Instance_Stage)\
        .filter(models.Test_Instance_Stage.id == test_stage_id)\
        .first()

def get_test_stages_for_test_instance(
    db: Session, 
    test_instance_id: int,
):
    return db.query(models.Test_Instance_Stage)\
        .filter(models.Test_Instance_Stage.test_instance_id == test_instance_id)\
        .all()

def get_test_stage_statuses(db: Session, test_stage_id: int):
    return db.query(models.Test_Instance_Stage_Status)\
        .filter(models.Test_Instance_Stage_Status.test_stage_id == test_stage_id)\
        .all()


# ---------------------------------------- #
# ------------ Test Instances ------------ #
# ---------------------------------------- #

def create_test_instance(db: Session, netapp_id: str, network_service_id: str, testbed_id: str, service_test_specification_id: str, testing_descriptor: dict = None, extra_information: str = None, nods_id:str = None):
    current_build = get_last_build_of_test_instance(db, netapp_id, network_service_id) + 1
    test_instance = models.Test_Instance(
        netapp_id=netapp_id,
        network_service_id=network_service_id,
        build=current_build,
        testbed_id=testbed_id,
        testing_descriptor=testing_descriptor,
        service_test_specification_id=service_test_specification_id,
        access_token=''.join(random.choice(string.ascii_lowercase) for i in range(16))
    )
    if extra_information:
        test_instance.extra_information = extra_information
    if nods_id:
        test_instance.nods_id = nods_id
    db.add(test_instance)
    db.commit()
    db.refresh(test_instance)

    create_test_status(
        db=db,
        test_id=test_instance.id,
        state=Constants.TestStatus.SUBMITTED_TO_CI_CD_MANAGER,
    )
    
    logging.info(f"Created test instance for netapp_id '{netapp_id}' and network_service_id '{network_service_id}'.")
    return test_instance


def update_test_instance_testing_descriptor(db: Session, test_id: int, testing_descriptor: str):
    db_test_instance = db.query(models.Test_Instance).filter(models.Test_Instance.id == test_id).first()
    db_test_instance.testing_descriptor = testing_descriptor
    db.commit()
    db.refresh(db_test_instance)
    logging.info(f"Updated testing_descriptor on test instance {db_test_instance.id}.")
    return db_test_instance

def update_test_instance_extra_info(db: Session, test_id: int, extra_information: str):
    db_test_instance = db.query(models.Test_Instance).filter(models.Test_Instance.id == test_id).first()
    db_test_instance.extra_information = extra_information
    db.commit()
    db.refresh(db_test_instance)
    logging.info(f"Updated extra information on test instance {db_test_instance.id}.")
    return db_test_instance

def get_all_test_instances(db: Session):
    return db.query(models.Test_Instance).all()

def create_test_instance_dev_defined(db: Session, test_instance_id: int, test_case_name: str, test_case_location: str):
    dev_defined_test_case_instance = models.Test_Instance_Developer_Defined_Test_Cases(
        test_instance_id=test_instance_id,
        test_case_name=test_case_name,
        test_case_location=test_case_location
    )
    db.add(dev_defined_test_case_instance)
    db.commit()
    db.refresh(dev_defined_test_case_instance)
    logging.info(f"Created dev-defined test case with id {dev_defined_test_case_instance.id}")
    return dev_defined_test_case_instance

def get_test_instance_dev_defined(db: Session, test_instance_id: int):
    return db.query(models.Test_Instance_Developer_Defined_Test_Cases)\
        .filter(
            models.Test_Instance_Developer_Defined_Test_Cases.test_instance_id == test_instance_id
        ).all()

def get_test_instance(db: Session, test_id: int, access_token: str = None):
    if access_token is None:
        db_test_instance = db.query(models.Test_Instance).filter(models.Test_Instance.id == test_id).first()
    else:
        db_test_instance = db.query(models.Test_Instance).filter(models.Test_Instance.id == test_id, models.Test_Instance.access_token == access_token).first()
    return db_test_instance


def update_test_instance_ci_cd_agent(db: Session, test_id: int, ci_cd_id: int):
    db_test_instance = db.query(models.Test_Instance).filter(models.Test_Instance.id == test_id).first()
    db_test_instance.ci_cd_node_id = ci_cd_id
    db.commit()
    db.refresh(db_test_instance)
    logging.info(f"Updated ci_cd_node agent on test instance {db_test_instance.id}.")
    return db_test_instance


def update_test_instance_after_validation_process(db: Session, test_id: int, test_log_location: str, test_results_location:str):
    db_test_instance = db.query(models.Test_Instance).filter(models.Test_Instance.id == test_id).first()
    db_test_instance.test_log_location = test_log_location
    db_test_instance.test_results_location = test_results_location
    db.commit()
    db.refresh(db_test_instance)
    logging.info(f"Updated test_results_location and test_log_location on test instance {db_test_instance.id}.")
    return db_test_instance
  

def get_test_instances_by_netapp_and_network_service(db: Session, netapp_id: str, network_service_id: str):
    return db.query(models.Test_Instance).filter(models.Test_Instance.netapp_id == netapp_id, models.Test_Instance.network_service_id == network_service_id).all()


def get_test_instances_by_id(db: Session, test_instance_id: int):
    return db.query(models.Test_Instance).filter(models.Test_Instance.id == test_instance_id).first().as_dict()


def get_last_build_of_test_instance(db: Session, netapp_id: str, network_service_id: str):
    return len(db.query(models.Test_Instance).filter(models.Test_Instance.netapp_id == netapp_id, models.Test_Instance.network_service_id == network_service_id).all())


def get_ci_cd_agent_given_test_instance_id(db: Session, test_instance_id: int):
    ci_cd_node_id = db.query(models.Test_Instance).filter(models.Test_Instance.id == test_instance_id).first().ci_cd_node_id
    return agents_crud.get_ci_cd_node_by_id(db, ci_cd_node_id)

def get_ci_cd_agents_given_test_instance_id(db: Session, test_instance_id: int):
    test_stages = get_test_stages_for_test_instance(db, test_instance_id)
    return [
        agents_crud.get_ci_cd_node_by_id(db, test_stage.testing_agent_id)
        for test_stage
        in test_stages
    ]


# ---------------------------------------- #
# -------------- Test Status ------------- #
# ---------------------------------------- #

def create_test_status(db: Session, test_id: int, state: str, description: str = None ,success: bool = True):
    test_status = models.Test_Status(test_id=test_id, state=state, description=description, success=success)
    db.add(test_status)
    db.commit()
    db.refresh(test_status)
    logging.info(f"Created test status: {test_status.as_dict()}")
    return test_status


def create_test_status_ci_cd_agent(db: Session, test_status: ci_cd_manager_schemas.Test_Status_Update):    
    # 1 - validate communication token
    if not is_communication_token_for_test_valid(db, test_status.test_id, test_status.communication_token):
        raise Exception("Communication Tokens don't match")
    # 2 - create status
    test_status = models.Test_Status(test_id=test_status.test_id, state=test_status.state.upper(), success=test_status.success)
    db.add(test_status)
    db.commit()
    db.refresh(test_status)
    logging.info(f"CI/CD Agent created test status: {test_status.as_dict()}")
    return test_status


def get_test_status_given_test_id(db: Session, test_id: int):
    return db.query(models.Test_Status).filter(models.Test_Status.test_id == test_id).all()


def get_all_test_status_for_test(db: Session, netapp_id: str, network_service_id: str):
    test_instances = get_test_instances_by_netapp_and_network_service(db, netapp_id, network_service_id)
    dic = {
        "netapp_id": netapp_id,
        "network_service_id": network_service_id,
        "test_status": {}
    }
    for t in test_instances:
        dic["test_status"]["Build " + str(t.build)] = [ts.as_dict() for ts in get_test_status_given_test_id(db, t.id)]
    return dic


def get_all_test_status_for_test_given_id(db: Session, test_id: int, access_token: str = None):
    if __validate_test_instance_access_token(db, test_id, access_token):
        db_test_instance = db.query(models.Test_Instance).filter(models.Test_Instance.id == test_id).first()
        test_status = get_test_status_given_test_id(db, test_id)
        return test_status



# ---------------------------------------- #
# ---------- Test Instance Tests --------- #
# ---------------------------------------- #

def create_test_instance_test(db: Session, test_instance_id: int, 
    test_stage_id: int, performed_test: str, original_test_name: str,
    description: str, performed_test_results_location: str = None,
    is_developer_defined=False, developer_defined_test_filepath = None):
    
    test_instance_test = models.Test_Instance_Tests(
        test_instance=test_instance_id,
        test_stage=test_stage_id,
        performed_test=performed_test,
        original_test_name=original_test_name,
        description=description,
        is_developer_defined=is_developer_defined,
        developer_defined_test_filepath=developer_defined_test_filepath
    )
    
    if performed_test_results_location:
        test_instance_test.performed_test_results_location = performed_test_results_location
    db.add(test_instance_test)
    db.commit()
    db.refresh(test_instance_test)
    #logging.info(f"Test Instance Test created : {test_instance_test.as_dict()}")
    return test_instance_test


def update_test_instance_test(db: Session, test_instance_id: int, performed_test: str, description: str, performed_test_results_location: str = None):
    test_instance_test = db.query(models.Test_Instance_Tests).filter(models.Test_Instance_Tests.test_instance == test_instance_id and 
    models.Test_Instance_Tests.performed_test == performed_test).first()
    test_instance_test.performed_test_results_location = performed_test_results_location
    test_instance_test.description = description
    db.commit()
    db.refresh(test_instance_test)
    logging.info(f"Test Instance Test update : {test_instance_test.as_dict()}")
    return test_instance_test


def get_tests_of_test_instance(db: Session, test_instance_id: int, access_token: str = None):
    if __validate_test_instance_access_token(db, test_instance_id, access_token):
        test_instance_tests = db.query(models.Test_Instance_Tests).filter(models.Test_Instance_Tests.test_instance == test_instance_id).all()
        return test_instance_tests


def update_test_status_of_test_instance(db: Session, test_instance_id: int, performed_test: str, start_time: str, end_time: str, success: bool):
    test_instance_test = db.query(models.Test_Instance_Tests).filter(models.Test_Instance_Tests.test_instance == test_instance_id, 
    models.Test_Instance_Tests.performed_test == performed_test).first()
    test_instance_test.start_time = start_time
    test_instance_test.end_time = end_time
    test_instance_test.success = success
    db.commit()
    db.refresh(test_instance_test)
    logging.info(f"Test Instance Test update : {test_instance_test.as_dict()}")
    return test_instance_test


def get_developer_defined_tests_for_test_instance(db: Session, 
    test_instance_id: int, communication_token: str = None):
    
    #if not is_communication_token_for_test_valid(db, test_instance_id, communication_token):
    #    raise Exception("Communication Tokens don't match")
    
    test_instance_tests = db.query(models.Test_Instance_Tests).filter(
            models.Test_Instance_Tests.test_instance == test_instance_id,
            models.Test_Instance_Tests.is_developer_defined == True
        ).all()
    return test_instance_tests


def get_developer_defined_test_for_test_instance(db: Session, 
    test_instance_id: int, communication_token: str, test_name: str):
    print(f"Test Instance = {test_instance_id}, Test Name = {test_name} ")
    # TODO: FIX
    #if not is_communication_token_for_test_valid(db, test_instance_id, communication_token):
    #    raise Exception("Communication Tokens don't match")
    test_instance_test = db.query(models.Test_Instance_Tests).filter(
            models.Test_Instance_Tests.test_instance == test_instance_id,
        models.Test_Instance_Tests.performed_test == test_name,
            
        ).first()
    print(test_instance_test.performed_test)
    print(test_instance_test.developer_defined_test_filepath)
    return test_instance_test.developer_defined_test_filepath
    
# ---------------------------------------- #
# ------------ Test Information ---------- #
# ---------------------------------------- #

def get_test_info_by_testbed_id(db: Session, testbed_id: str):
    return (
        db.query(models.Test_Information)
        .options(joinedload(models.Test_Information.testinfo_variables)
                 .joinedload(models.Test_Variables.possible_options))
        .filter(models.Test_Information.testbed_id == testbed_id)
        .all()
    )

def is_testinfo_valid(db: Session, test_info_instances: models.Test_Information,
testinfo_data:testinfo_schemas.TestInformation):
    return all( [t.testid != testinfo_data.testid for t in test_info_instances])

def create_testinfo_variables(db: Session, testinfo_data: testinfo_schemas.TestInformation):
    lst = []
    for variable in testinfo_data.test_variables:
        options = [ models.Variable_Options(name=option) for option in variable.possible_options]
        obj = models.Test_Variables(
            variable_name=variable.variable_name,
            description=variable.description,
            mandatory=variable.mandatory,
            type=variable.type,
            possible_options=options
            )
        lst.append(obj)
    return lst


def create_test_information(db: Session,testinfo_data: testinfo_schemas.TestInformation):
    testbed = get_testbed_by_id(db,testinfo_data.testbed_id)
    if not testbed:
        return False,"The selected testbed does not exit"
    
    test_info_instances = get_test_info_by_testbed_id(
        db,testinfo_data.testbed_id
    )

    # Verify if already exists a test with the same id in the testbed
    test_info_instance = db.query(models.Test_Information).filter(
        models.Test_Information.testbed_id == testinfo_data.testbed_id,
        models.Test_Information.testid == testinfo_data.testid,
        ).first()
    
    
    if test_info_instance:

        test_info_instance_id = test_info_instance.testid

        logging.info(
            f"The testbed '{testbed.name}' already contains information " +
            f"about a test with the id {testinfo_data.testid}. Will update it!"
        )
         
        db.begin_nested()
        try:
            # Delete current test info variables
            for test_info_variable in test_info_instance.testinfo_variables:
                db.delete(test_info_variable)
                db.flush()
            
            # Create new test info variables
            test_info_variables = create_testinfo_variables(db,testinfo_data)
            
            # Udpate the current test instance
            test_info_instance.name=testinfo_data.name,
            test_info_instance.description=testinfo_data.description,
            test_info_instance.ftp_base_location=testinfo_data.ftp_base_location,
            test_info_instance.test_filename=testinfo_data.test_filename,
            test_info_instance.test_type=testinfo_data.test_type,
            test_info_instance.testinfo_variables=test_info_variables

            db.commit()
            logging.info(
                f"Updated test instance '{test_info_instance_id}' in " +
                f"testbed '{test_info_instance.testbed_id}'."
            )
            
            return test_info_instance, ""
        except Exception as e:
            logging.error(
                f"Failed to update test instance '{test_info_instance_id}'" +
                f" in testbed '{test_info_instance.testbed_id}'. Due to: " +
                f"Exception {e}.\n Rolling back..."
            )
            db.rollback()
            logging.error("Rollback completed.")
            return None
        
    testinfo_variables = create_testinfo_variables(db,testinfo_data)
    
    test_info_instance = models.Test_Information(
        testid=testinfo_data.testid,
        name=testinfo_data.name,
        testbed_id=testinfo_data.testbed_id,
        description=testinfo_data.description,
        ftp_base_location=testinfo_data.ftp_base_location,
        test_filename=testinfo_data.test_filename,
        test_type=testinfo_data.test_type,
        testinfo_variables=testinfo_variables
    )
    db.add(test_info_instance)
    db.commit()
    db.refresh(test_info_instance)
    
    logging.info(
        f"Updated test instance '{test_info_instance.testid}' in " +
        f"testbed '{test_info_instance.testbed_id}'."
    )

    return test_info_instance,""
    

# ---------------------------------------- #
# ----------- Testing Artifact------------ #
# ---------------------------------------- #


def create_testing_artifact(db: Session, test_instance_id: int, 
                            ftp_base_path: str):
    
    testing_artifact_db = db.query(models.Testing_Artifact).filter(
        models.Testing_Artifact.test_instance_id == test_instance_id).first()
    
    if testing_artifact_db is not None:
        update_testing_artifact(db, test_instance_id, ftp_base_path)
  
    testing_artifact_db = models.Testing_Artifact(
        test_instance_id=test_instance_id,
        ftp_base_path=ftp_base_path,
    )
    
    db.add(testing_artifact_db)
    db.commit()
    db.refresh(testing_artifact_db)
    logging.info(f"Testing Artifacts Created : {testing_artifact_db.as_dict()}")
    return testing_artifact_db


def update_testing_artifact(db: Session, test_instance_id: int, 
                            ftp_base_path: str):
    
    testing_artifact_db = db.query(models.Testing_Artifact).filter(
        models.Testing_Artifact.test_instance_id == test_instance_id).first()
    
    testing_artifact_db.ftp_base_path = ftp_base_path    
    db.commit()
    db.refresh(testing_artifact_db)
    logging.info(f"Testing Artifacts Updated : {testing_artifact_db.as_dict()}")
    return testing_artifact_db


def get_testing_artifact_base_path(db: Session, 
    test_instance_id: int, communication_token: str = None):
    
    # TODO: Fix this later
    #if not is_communication_token_for_test_valid(db, test_instance_id, communication_token):
    #    raise Exception("Communication Tokens don't match")
    
    testing_artifact_db = db.query(models.Testing_Artifact).filter(
        models.Testing_Artifact.test_instance_id == test_instance_id).first()
    
    return testing_artifact_db.ftp_base_path



# ---------------------------------------- #
# ----------------- Utils ---------------- #
# ---------------------------------------- #

def is_communication_token_for_test_valid(db: Session, test_instance_id: int, communication_token: str):
    # 1 get the CI/CD Agent for the test instance
    db_test_instance = db.query(models.Test_Instance).filter(models.Test_Instance.id == test_instance_id).first()
    db_ci_cd_node = db.query(models.CI_CD_Agent).filter(models.CI_CD_Agent.id == db_test_instance.ci_cd_node_id).first()
    
    # 2 -check if the communication token is ok
    if db_ci_cd_node.communication_token != communication_token:
        return False
    return True


def get_test_base_information(db: Session, test_instance_id: int, access_token: str = None):
    if __validate_test_instance_access_token(db, test_instance_id, access_token):
        db_test_instance = db.query(models.Test_Instance).filter(models.Test_Instance.id == test_instance_id).first()      
        all_test_status = get_all_test_status_for_test_given_id(db, test_instance_id)
        starting_time = all_test_status[0].timestamp
        test_status = all([ts.success for ts in all_test_status])
        
        # Involved Testing Agents
        testing_agents = set(get_ci_cd_agents_given_test_instance_id(db, test_instance_id))
        test_cases = get_tests_of_test_instance(db, test_instance_id, access_token)
        test_stages = get_test_stages_for_test_instance(db, test_instance_id)

        testing_agents_info = []
        for testing_agent in testing_agents:

            agent_stages = [
                stage
                for stage
                in test_stages
                if stage.testing_agent_id == testing_agent.id
            ]

            testing_agents_info.append(
                {
                    "testing_agent_id": testing_agent.id,
                    "testing_agent_type": testing_agent.type.value.upper() if testing_agent.type == models.AgentType.CUSTOM else "TESTBED_DEFAULT",
                    "performed_testing_stages": len(agent_stages),
                    "performed_test_cases": len({
                        test_case.performed_test
                        for test_case
                        in test_cases
                        if test_case.test_stage in [stage.id for stage in agent_stages]
                    }),
                    "name": testing_agent.name if testing_agent.type == models.AgentType.CUSTOM else "Not Applicable",
                    "service_order": testing_agent.service_order if testing_agent.type == models.AgentType.CUSTOM else "Not Applicable",
                    "url": testing_agent.url,
                    "username": testing_agent.username if testing_agent.type == models.AgentType.CUSTOM else "Not Disclosed",
                    "password": testing_agent.password if testing_agent.type == models.AgentType.CUSTOM else "Not Disclosed",
                }
            )

        all_test_status = [t.as_dict() for t in all_test_status]
        for status in all_test_status:
            status["state"] = status["state"].value

        return { 
            "test_instance": {
                "test_id": db_test_instance.id,
                "netapp_id": db_test_instance.netapp_id,
                "network_service_id": db_test_instance.network_service_id,
                "testbed_id": db_test_instance.testbed_id,
                "started_at": str(starting_time),
                "overall_test_status": test_status,
                "test_status": all_test_status,
                "testing_descriptor": yaml.dump(db_test_instance.testing_descriptor)
            },
            "test_agents": testing_agents_info
        }

def __validate_test_instance_access_token(db: Session, test_instance_id: int, access_token: str = None):
    if access_token is not None:
        db_test_instance = db.query(models.Test_Instance).filter(models.Test_Instance.id == test_instance_id, models.Test_Instance.access_token == access_token).first()   
        if not db_test_instance: 
            logging.info(f"Invalid access_token for test_instance_id {test_instance_id}.")
            return False
    return True
