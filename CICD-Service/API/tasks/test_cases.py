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
import test_helpers.developer_defined as dev_defined_test_helpers
from datetime import timedelta
from background_tasks import metrics_and_logs 
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

def register_test_cases_for_test_instance(test_instance_id: int):
    logging.debug(f"Validating test cases for test instance: {test_instance_id}")
    # Here would go the logic to validate the test cases
    validate_test_cases_for_test_instance(test_instance_id)
    logging.debug(
        f"Finished validating test cases for test instance: {test_instance_id}"
    )

def validate_test_cases_for_test_instance(test_instance_id: int):
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
            f"All test parameters of Test Instance "
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
                state=Constants.TestStatus.TESTING_PROCESS_ENDED,
                description="Test ended due to invalid test cases.",
                success=False
            )

@broker.task
async def obtain_dev_defined_test_cases_for_test_instance(test_instance_id: int):
    with get_db() as db:
        test_instance = crud.get_test_instances_by_id(db, test_instance_id)

        developer_defined_tests = [testcase["name"] 
            for testcase 
            in test_instance["testing_descriptor"]['testcases'] 
            if testcase["type"] == 'developer-defined'
        ]

        if len(developer_defined_tests) > 0:

            logging.info(
                f"Found {len(developer_defined_tests)} developer defined tests "
                f"for test instance: {test_instance_id}. "
                f"Developer Defined Tests: {str(developer_defined_tests)}"
                )

            try:
                # TODO: Authentication with the NODS should be a decorator
                success, token =  Utils.get_nods_token()

                # Get the Service Test Specification from NODS
                success, response = Utils.get_serviceTestSpecification(
                    token=token,
                    _id=test_instance["service_test_specification_id"]
                )

                # Get attachments
                attachments = {attachment['name']: attachment['url']
                    for attachment 
                    in response['attachment']
                }

                # Obtain developer defined tests
                dev_defined_obtained_tests = dev_defined_test_helpers.load_developer_defined_tests(
                    token, developer_defined_tests, attachments, test_instance["nods_id"])
                
                # Store Test Location in Database
                for name, location in dev_defined_obtained_tests.items():
                    crud.create_test_instance_dev_defined(
                        db=db,
                        test_instance_id=test_instance_id,
                        test_case_name=name,
                        test_case_location=location
                    )

                crud.create_test_status(
                    db=db,
                    test_id=test_instance_id,
                    state=Constants.TestStatus.DEVELOPER_DEFINED_TESTS_OBTAINED,
                    description=f"Developer Defined Tests: {str(dev_defined_obtained_tests)}",
                    success=True
                )

            except Exception as e:
                crud.create_test_status(
                    db=db,
                    test_id=test_instance_id,
                    state=Constants.TestStatus.DEVELOPER_DEFINED_TESTS_OBTAINED,
                    description=f"Unable to Obtain the Developer Defined Tests from NODS - {e}",
                    success=False
                )
                crud.create_test_status(
                    db=db,
                    test_id=test_instance_id,
                    state=Constants.TestStatus.TESTING_PROCESS_ENDED,
                    description=f"Unable to Obtain the Developer Defined Tests from NODS - {e}",
                    success=False
                )