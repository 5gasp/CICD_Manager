from tasks.broker import broker
from sql_app.schemas import TMF653 as tmf653_schemas
import aux.utils as Utils
from aux import startup
from test_helpers import test_descriptor_render, testing_artifacts
from sql_app.database import SessionLocal
from sqlalchemy.orm import Session
from contextlib import contextmanager
from sql_app import crud
import logging
import aux.constants as Constants
from testing_descriptors_validator.test_descriptor_validator import Test_Descriptor_Validator
from datetime import timedelta

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


@broker.task(schedule=[{"cron": "*/1 * * * *", "args": [1]}])
async def heavy_task(value: int) -> int:
    with get_db() as db:
        test_instances = crud.get_all_test_instances(db)

        for test_instance in test_instances:
            test_statuses = {
                test_status.state: test_status.success
                for test_status
                in crud.get_test_status_given_test_id(db, test_instance.id)
            }

            # Invoke the Registration of Test Cases if not done yet
            if (
                Constants.TestStatus.TEST_CASES_VALIDATED_FOR_TESTBED not in test_statuses
                and test_statuses.get(
                    Constants.TestStatus.TESTING_TESTBED_VALIDATED, False
                )
            ):
                logging.info(f"Will register the testcases for test instance: {test_instance.id}")
                task = await register_test_cases_for_test_instance.kiq(test_instance.id)
            
            # Invoke the downloading of developer defined tests if not done yet
            if (
                Constants.TestStatus.DEVELOPER_DEFINED_TESTS_OBTAINED not in test_statuses
                and test_statuses.get(
                    Constants.TestStatus.TEST_CASES_VALIDATED_FOR_TESTBED, False
                )
            ):
                logging.info(f"Will configure monitoring for test instance: {test_instance.id}")
                #task = await testing_artifacts.configure_application_monitoring_for_test_instance.kiq(test_instance.id)


            # Invoke the configuration of monitoring if not done yet
            if (
                Constants.TestStatus.APPLICATION_MONITORING_CONFIGURED not in test_statuses
                and test_statuses.get(
                    Constants.TestStatus.TEST_CASES_VALIDATED_FOR_TESTBED, False
                )
            ):
                logging.info(f"Will configure monitoring for test instance: {test_instance.id}")
                #task = await testing_artifacts.configure_application_monitoring_for_test_instance.kiq(test_instance.id)


            # Invoke the configuration of logging if not done yet
            if (
                Constants.TestStatus.APPLICATION_LOGGING_CONFIGURED not in test_statuses
                and test_statuses.get(
                    Constants.TestStatus.TEST_CASES_VALIDATED_FOR_TESTBED, False
                )
            ):
                logging.info(f"Will configure logging for test instance: {test_instance.id}")
                #task = await testing_artifacts.configure_application_logging_for_test_instance.kiq(test_instance.id)
            

            # Invoke the provisioingng of custom CI/CD agents if not done yet
            if (
                Constants.TestStatus.CUSTOM_CI_CD_AGENTS_PROVISIONED_STARTED not in test_statuses
                and test_statuses.get(
                    Constants.TestStatus.TEST_CASES_VALIDATED_FOR_TESTBED, False
                )
            ):
                logging.info(f"Will provisiong the CI/CD Agents for test instance: {test_instance.id}")
                #task = await testing_artifacts.configure_application_logging_for_test_instance.kiq(test_instance.id)



@broker.task
async def register_test_cases_for_test_instance(test_instance_id: int):
    logging.debug(f"Validating test cases for test instance: {test_instance_id}")
    # Here would go the logic to validate the test cases
    task = await validate_test_cases_for_test_instance(test_instance_id)
    logging.debug(
        f"Finished validating test cases for test instance: {test_instance_id}"
    )

@broker.task
async def validate_test_cases_for_test_instance(test_instance_id: int):
    with get_db() as db:
        test_instance = crud.get_test_instances_by_id(db, test_instance_id)
        testbed_tests = crud.get_test_info_by_testbed_id(db, test_instance["testbed_id"])

    test_descriptor_validator = Test_Descriptor_Validator(
        test_instance["testing_descriptor"]
    )

    errors = test_descriptor_validator.validate_tests_parameters(testbed_tests)
    if len(errors) != 0:
        logging.error(
            f"Error on validating test parameters of Test " 
            f"Instance {test_instance_id} - {errors}")
    else:
        logging.info(
            f"All test parameters  of Test Instance "
            f"{test_instance_id} are valid."
        )
    
    with get_db() as db:
        crud.create_test_status(
            db=db,
            test_id=test_instance_id,
            state=Constants.TestStatus.TEST_CASES_VALIDATED_FOR_TESTBED,
            description=f"Errors: {errors}",
            success=len(errors) == 0
        )

        if len(errors) != 0:
            crud.create_test_status(
                db=db,
                test_id=test_instance_id,
                state=Constants.TestStatus.TEST_ENDED,
                description="Test ended due to invalid test cases.",
                success=False
            )