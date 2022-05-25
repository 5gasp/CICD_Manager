# -*- coding: utf-8 -*-
# @Author: Rafael Direito
# @Date:   22-05-2022 10:25:05
# @Email:  rdireito@av.it.pt
# @Last Modified by:   Rafael Direito
# @Last Modified time: 25-05-2022 13:11:37
# @Description: Contains several constant variables needed in the workflow of the
# CI/CD Manager

# DEVELOPER DEFINED TESTS
DEVELOPER_DEFINED_TEST_TEMP_STORAGE_DIR = "warehouse/developer-defined-tests"
DEVELOPER_DEFINED_TEST_BASE_FTP_DIR = "developer-defined-tests"

# AUTH
SECRET_KEY = "99cb3e97787cf81a7f418c42b96a06f77ce25ddbb2f7f83a53cf3474896624f9"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
DEFAULT_ADMIN_CREDENTIALS = {
    "username": "admin",
    "password": "admin"
}
USER_ROLES = ["ADMIN", "USER"]

# CI/CD MANAGER 
CI_CD_MANAGER_URL = None

# TEST/TESTBED INFO
TEST_INFO = None
TEST_INFO_FILEPATH = None
TESTBED_INFO_FILEPATH = None

# Metrics Collection Info
METRICS_COLLECTION_INFO = None
METRICS_COLLECTION_INFO_FILEPATH = None

# FTP
FTP_RESULTS_USER = None
FTP_RESULTS_PASSWORD = None
FTP_RESULTS_URL = None

# Database
DB_NAME = None
DB_LOCATION = None
DB_USER = None
DB_PASSWORD = None

# Metrics Repository
MR_LOCATION = None
MR_DB = None

#NODS
NODS_USER=None
NODS_PASSWORD=None
NODS_HOST=None

#TRVD
TRVD_HOST=None

# Testbeds
TESTBEDS_INFO = None

# Possible Test Status
TEST_STATUS ={
    "submitted_on_manager": "SUBMITTED_TO_CI_CD_MANAGER",
    "ci_cd_agent_provisioned": "PROVISIONED_CI_CD_AGENT",
    "ci_cd_agent_auth": "AUTHENTICATED_ON_CI_CD_AGENT",
    "created_comm_token": "CREATED_COMMUNICATION_TOKEN_ON_CI_CD_AGENT",
    "created_pipeline_script": "CREATED_PIPELINE_SCRIPT",
    "submitted_pipeline_script": "SUBMITTED_PIPELINE_SCRIPT",
    "ci_cd_agent_setup_environment": "ENVIRONMENT_SETUP_CI_CD_AGENT",
    "monitoring_started": "STARTED_MONITORING",
    "ci_cd_agent_obtained_tests": "OBTAINED_TESTS_ON_CI_CD_AGENT",
    "ci_cd_agent_performed_tests": "PERFORMED_TESTS_ON_CI_CD_AGENT",
    "ci_cd_agent_created_logs": "CREATED_LOGS_ON_CI_CD_AGENT",
    "monitoring_ended": "ENDED_MONITORING",
    "ci_cd_agent_published_test_results": "PUBLISHED_TEST_RESULTS",
    "ci_cd_agent_cleaned_test_environment": "CLEANED_TEST_ENVIRONMENT",
    "test_ended": "TEST_ENDED",
    "obtained_metrics_collection_files": "OBTAINED_METRICS_COLLECTION_FILES",
}
