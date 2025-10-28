# -*- coding: utf-8 -*-
# @Author: Daniel Gomes (dagomes@av.it.pt),
# @Date:   22-05-2022 10:25:05
# @Email:  rdireito@av.it.pt
# @Last Modified by:   Rafael Direito
# @Last Modified time: 25-05-2022 10:57:34
# @Description: Contains several functions that should be invoked on startup

# custom imports
import aux.constants as Constants
from sql_app.CRUD import auth as CRUD_Auth

# generic imports
import configparser
import logging
import yaml
import os
import inspect
import ftputil

# Logger
logging.basicConfig(
    format="%(module)-15s:%(levelname)-10s| %(message)s",
    level=logging.INFO
)
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))


def load_config():
    # load config
    config = configparser.ConfigParser()
    config.read('config.ini')
    print(config)
    # Test config
    try:
        # Load Variables
        Constants.FTP_RESULTS_USER = config['RESULTS_FTP']['User']
        Constants.FTP_RESULTS_PASSWORD = config['RESULTS_FTP']['Password']
        Constants.FTP_RESULTS_URL = config['RESULTS_FTP']['Url']
        Constants.FTP_LTR_USER = config['LTR_FTP']['User']
        Constants.FTP_LTR_PASSWORD = config['LTR_FTP']['Password']
        Constants.FTP_LTR_URL = config['LTR_FTP']['Url']
        Constants.CI_CD_MANAGER_URL = config['CI_CD_MANAGER']['Url']
        Constants.TEST_INFO_FILEPATH = config['DESCRIPTORS_LOCATION']['Tests_Information_Descriptor_Filepath']
        Constants.TESTBED_INFO_FILEPATH = config['DESCRIPTORS_LOCATION']['Testbeds_Information_Descriptor_Filepath']
        Constants.METRICS_COLLECTION_INFO_FILEPATH = config['DESCRIPTORS_LOCATION']['Metrics_Collection_Information_Descriptor_Filepath']
        Constants.DB_LOCATION = config['DB']['Location']
        Constants.DB_NAME = config['DB']['Name']
        Constants.DB_USER = config['DB']['User']
        Constants.DB_PASSWORD = config['DB']['Password']
        Constants.MR_LOCATION = config['METRICS-REPOSITORY']['InfluxDB_Location']
        Constants.MR_DB = config['METRICS-REPOSITORY']['DB_Name']
        Constants.NODS_HOST = config['NODS']['Host']
        Constants.NODS_USER = config['NODS']['User']
        Constants.NODS_PASSWORD = config['NODS']['Password']
        Constants.TRVD_HOST = config['TRVD']['Host']

        Constants.PROMETHEUS_TARGET_UPDATE_API = config['PROMETHEUS']['TargetsUpdateAPI']
        Constants.GRAFANA_DATASOURCE_UID = config['GRAFANA']['DatasourceUID']
        Constants.GRAFANA_USERNAME = config['GRAFANA']['Username']
        Constants.GRAFANA_PASSWORD = config['GRAFANA']['Password']
        Constants.GRAFANA_IP_OR_DOMAIN = config['GRAFANA']['IPorDomain']
        Constants.GRAFANA_PORT = config['GRAFANA']['Port']
        Constants.DASHBOARD_UID_LENGTH = config['GRAFANA']['DashboardUIDLength']
        Constants.KIBANA_USERNAME = config['KIBANA']['Username']
        Constants.KIBANA_PASSWORD = config['KIBANA']['Password']
        Constants.KIBANA_IP_OR_DOMAIN = config['KIBANA']['IPorDomain']
        Constants.KIBANA_PORT = config['KIBANA']['Port']
        
    except Exception as e:
        print(e)
        print("-----")
        return False, """The config file should have the folling sections with the following variables: 
        FTP -> User, Password, Url | CI_CD_MANAGER -> Url | DESCRIPTORS_LOCATION -> Tests_Information_Descriptor_Filepath, 
        Testbeds_Information_Descriptor_Filepath, Metrics_Collection_Information_Descriptor_Filepath | DB -> Location, 
        Name, User, Password | METRICS-REPOSITORY -> InfluxDB_Location, DB_Name"""
    return True, ""


def load_test_info():
    with open(Constants.TEST_INFO_FILEPATH) as file:
        TEST_INFO = yaml.load(file, Loader=yaml.FullLoader)


def load_metrics_collection_info():
    try:
        with open(Constants.METRICS_COLLECTION_INFO_FILEPATH) as file:
            Constants.METRICS_COLLECTION_INFO = yaml.load(file, Loader=yaml.FullLoader)
    except:
        return False, "Could not load the metrics collection information"
    return True, ""


def startup_roles(db):
    for role in Constants.USER_ROLES:
        CRUD_Auth.create_role(db, role)


def create_default_admin(db):
    CRUD_Auth.register_user(
        db = db, 
        username = Constants.DEFAULT_ADMIN_CREDENTIALS['username'], 
        password = Constants.DEFAULT_ADMIN_CREDENTIALS['password'],
        roles = Constants.USER_ROLES)
    

def create_dir_to_store_developer_defined_tests():
    ddt_dir = Constants.DEVELOPER_DEFINED_TEST_TEMP_STORAGE_DIR
    if not os.path.exists(ddt_dir):
        os.makedirs(ddt_dir)
    logging.info(f"Directory to store developer defined tests: {ddt_dir}")
    

def create_dir_to_store_testing_artifacst():
    ddt_dir = Constants.TESTING_ARTIFACTS_FTP_TEMP_STORAGE_DIR
    if not os.path.exists(ddt_dir):
        os.makedirs(ddt_dir)
    logging.info(f"Directory to testing artifacts: {ddt_dir}")


def create_dir_to_store_developer_defined_tests_ftp():
    try:
        # Check if base dir exists
        ftp_host = Constants.FTP_RESULTS_URL.split(":")[0]
        with ftputil.FTPHost(ftp_host, Constants.FTP_RESULTS_USER, 
                             Constants.FTP_RESULTS_PASSWORD) as ftp_host:

            # If the root directory does not exist, create it
            if not ftp_host.path.isdir(
                    Constants.DEVELOPER_DEFINED_TEST_BASE_FTP_DIR
                ):
                logging.info("Root directory for the developer defined tests "\
                    "does not exist. Creating it...")
            
                ftp_host.mkdir(Constants.DEVELOPER_DEFINED_TEST_BASE_FTP_DIR)
                
                logging.info("Developer Defined Tests directory was created!")
            else:
                logging.info("Developer Defined Tests directory was already "\
                    "created!")
    
    except Exception as e:
        raise Exception("Impossible to create FTP Developer Defined Tests "\
            f"directory: {e}"
        )


def create_dir_to_store_testing_artifacts_ftp():
    try:
        # Check if base dir exists
        ftp_host = Constants.FTP_RESULTS_URL.split(":")[0]
        with ftputil.FTPHost(ftp_host, Constants.FTP_RESULTS_USER, 
                             Constants.FTP_RESULTS_PASSWORD) as ftp_host:

            # If the root directory does not exist, create it
            if not ftp_host.path.isdir(
                    Constants.TESTING_ARTIFACTS_FTP_ROOT_PATH
                ):
                logging.info("Root directory for the testing artifacts "\
                    "does not exist. Creating it...")
            
                ftp_host.mkdir(Constants.TESTING_ARTIFACTS_FTP_ROOT_PATH)
                
                logging.info("Testing artifacts directory was created!")
            else:
                logging.info("Testing artifacts directory was already "\
                    "created!"
                )
    
    except Exception as e:
        raise Exception("Impossible to create testing artifacts "\
            f"directory: {e}"
        )


def create_dir_to_store_5gasp_default_testing_artifacts_ftp():
    try:
        # Check if base dir exists
        ftp_host = Constants.FTP_RESULTS_URL.split(":")[0]
        with ftputil.FTPHost(ftp_host, Constants.FTP_RESULTS_USER, 
                             Constants.FTP_RESULTS_PASSWORD) as ftp_host:

            # If the root directory does not exist, create it
            if not ftp_host.path.isdir(
                    Constants.DEFAULT_5GASP_TESTING_ARTIFACTS_FTP_ROOT_PATH
                ):
                logging.info("Root directory for the defautl testing "\
                    "artifacts does not exist. Creating it...")
            
                ftp_host.mkdir(
                    Constants.DEFAULT_5GASP_TESTING_ARTIFACTS_FTP_ROOT_PATH
                )
                
                logging.info("Testing artifacts default directory was "\
                    "created!"
                )
            else: 
                logging.info("Testing artifacts default directory was "\
                    "already created!"
                )
    
    except Exception as e:
        raise Exception("Impossible to create testing artifacts default"\
            f"directory: {e}"
        )