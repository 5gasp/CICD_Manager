from tasks.broker import broker
from tasks import metrics_and_logs, test_cases
import aux.utils as Utils
from aux import startup
from sql_app.database import SessionLocal
from sqlalchemy.orm import Session
from contextlib import contextmanager
from sql_app import crud
import logging
import aux.constants as Constants
from testing_descriptors_validator.test_descriptor_validator import Test_Descriptor_Validator
import test_helpers.developer_defined as dev_defined_test_helpers


startup.load_config()

# Logger
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
    datefmt="%d-%m-%Y %H:%M:%S.%f"
)

# Dependency
@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def is_next_state(test_statuses: dict, next_state: Constants.TestStatus):
    return next_state not in test_statuses and test_statuses.get(
        Constants.TestStatus.TEST_CASES_VALIDATED_FOR_TESTBED, False
    )

@broker.task(schedule=[{"cron": "*/1 * * * *"}])
async def lcm_engine() -> int:
    with get_db() as db:
        test_instances = crud.get_all_test_instances(db)

        for test_instance in test_instances:
            test_statuses = {
                test_status.state: test_status.success
                for test_status
                in crud.get_test_status_given_test_id(db, test_instance.id)
            }
           
            # Invoke the registration of test cases if not done yet
            if Constants.TestStatus.TESTING_DESCRIPTOR_VALIDATED in test_statuses and \
                Constants.TestStatus.TEST_CASES_VALIDATED_FOR_TESTBED not in test_statuses and \
                Constants.TestStatus.TEST_ENDED not in test_statuses:
                logging.info(f"Will register the testcases for test instance: {test_instance.id}")
                test_cases.register_test_cases_for_test_instance(test_instance.id)
                # Refresh test statuses to force the next stages to take place in the same cycle
                test_statuses = {
                    test_status.state: test_status.success
                    for test_status
                    in crud.get_test_status_given_test_id(db, test_instance.id)
                }
            
            # Invoke the downloading of developer defined tests if not done yet
            if is_next_state(test_statuses, Constants.TestStatus.DEVELOPER_DEFINED_TESTS_OBTAINED):
                logging.info(
                    f"Will download dev-defined test cases for test "
                    f"instance: {test_instance.id}"
                )
                await test_cases.obtain_dev_defined_test_cases_for_test_instance.kiq(test_instance.id)

            # Invoke the configuration of monitoring if not done yet
            if is_next_state(test_statuses, Constants.TestStatus.APPLICATION_MONITORING_CONFIGURED):
                logging.info(f"Will configure monitoring for test instance: {test_instance.id}")
                await metrics_and_logs.configure_monitoring_for_test_instance.kiq(test_instance.id)

            # Invoke the configuration of logging if not done yet
            if is_next_state(test_statuses, Constants.TestStatus.APPLICATION_LOGGING_CONFIGURED):
                logging.info(f"Will configure logging for test instance: {test_instance.id}")
                await metrics_and_logs.configure_logging_for_test_instance.kiq(test_instance.id)

            # Invoke the provisioingng of custom CI/CD agents if not done yet
            if is_next_state(test_statuses, Constants.TestStatus.CUSTOM_CI_CD_AGENTS_PROVISIONED_STARTED):
                logging.info(f"Will provisiong the CI/CD Agents for test instance: {test_instance.id}")
                #task = await testing_artifacts.configure_application_logging_for_test_instance.kiq(test_instance.id)
