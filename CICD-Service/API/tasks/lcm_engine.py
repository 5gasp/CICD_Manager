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

#roker.task
#ync def register_test_cases_for_test_instance(test_instance_id: int):
#  logging.debug(f"Validating test cases for test instance: {test_instance_id}")
#  # Here would go the logic to validate the test cases
#  task = await validate_test_cases_for_test_instance.kiq(test_instance_id)
#  await task.wait_result(timeout=15)
#  logging.debug(
#      f"Finished validating test cases for test instance: {test_instance_id}"
#  )
#  await lcm_engine.kiq()
#
#roker.task
#ync def validate_test_cases_for_test_instance(test_instance_id: int):
#  with get_db() as db:
#      test_instance = crud.get_test_instances_by_id(db, test_instance_id)
#      testbed_tests = crud.get_test_info_by_testbed_id(db, test_instance["testbed_id"])
#
#  test_descriptor_validator = Test_Descriptor_Validator(
#      test_instance["testing_descriptor"]
#  )
#
#  errors = test_descriptor_validator.validate_tests_parameters(testbed_tests)
#  if len(errors) != 0:
#      logging.error(
#          f"Error on validating test parameters of Test " 
#          f"Instance {test_instance_id} - {errors}")
#  else:
#      logging.info(
#          f"All test parameters of Test Instance "
#          f"{test_instance_id} are valid."
#      )
#  
#  with get_db() as db:
#      crud.create_test_status(
#          db=db,
#          test_id=test_instance_id,
#          state=Constants.TestStatus.TEST_CASES_VALIDATED_FOR_TESTBED,
#          description=f"Errors: {errors}",
#          success=len(errors) == 0
#      )
#
#      if len(errors) != 0:
#          crud.create_test_status(
#              db=db,
#              test_id=test_instance_id,
#              state=Constants.TestStatus.TEST_ENDED,
#              description="Test ended due to invalid test cases.",
#              success=False
#          )
#
#roker.task
#ync def obtain_dev_defined_test_cases_for_test_instance(test_instance_id: int):
#  with get_db() as db:
#      test_instance = crud.get_test_instances_by_id(db, test_instance_id)
#
#      developer_defined_tests = [testcase["name"] 
#          for testcase 
#          in test_instance["testing_descriptor"]['test_phases']['setup']['testcases'] 
#          if testcase["type"] == 'developer-defined'
#      ]
#
#      if len(developer_defined_tests) > 0:
#
#          logging.info(
#              f"Found {len(developer_defined_tests)} developer defined tests "
#              f"for test instance: {test_instance_id}. "
#              f"Developer Defined Tests: {str(developer_defined_tests)}"
#              )
#
#          try:
#              # TODO: Authentication with the NODS should be a decorator
#              success, token =  Utils.get_nods_token()
#
#              # Get the Service Test Specification from NODS
#              success, response = Utils.get_serviceTestSpecification(
#                  token=token,
#                  _id=test_instance["service_test_specification_id"]
#              )
#
#              # Get attachments
#              attachments = {attachment['name']: attachment['url']
#                  for attachment 
#                  in response['attachment']
#              }
#
#              # Obtain developer defined tests
#              dev_defined_obtained_tests = dev_defined_test_helpers.load_developer_defined_tests(
#                  token, developer_defined_tests, attachments, test_instance["nods_id"])
#
#              crud.create_test_status(
#                  db=db,
#                  test_id=test_instance_id,
#                  state=Constants.TestStatus.DEVELOPER_DEFINED_TESTS_OBTAINED,
#                  description=f"Developer Defined Tests: {str(dev_defined_obtained_tests)}",
#                  success=True
#              )
#
#          except Exception as e:
#              crud.create_test_status(
#                  db=db,
#                  test_id=test_instance_id,
#                  state=Constants.TestStatus.DEVELOPER_DEFINED_TESTS_OBTAINED,
#                  description=f"Unable to Obtain the Developer Defined Tests from NODS - {e}",
#                  success=False
#              )
#              crud.create_test_status(
#                  db=db,
#                  test_id=test_instance_id,
#                  state=Constants.TestStatus.TEST_ENDED,
#                  description=f"Unable to Obtain the Developer Defined Tests from NODS - {e}",
#                  success=False
#              )
#
#
#
#roker.task
#ync def configure_monitoring_for_test_instance(test_instance_id: int):
#
#  metrics_collection_info = None
#
#  # Get Testing Descriptor and obtain metrics collection info
#  with get_db() as db:
#      test_instance = crud.get_test_instances_by_id(db, test_instance_id)
#      
#      metrics_collection_info = test_instance["testing_descriptor"].get(
#          "metrics_collection", None
#      )
#
#  if metrics_collection_info:
#      logging.info(
#          "Will configure metrics collection for test "
#          f"instance: {test_instance_id}"
#      )
#
#      with get_db() as db:
#
#          success, errors = metrics_and_logs.parse_metrics_collection_info(
#              db, test_instance_id, metrics_collection_info
#          )
#
#          if success:
#              crud.create_test_status(
#                  db=db,
#                  test_id=test_instance_id,
#                  state=Constants.TestStatus.APPLICATION_MONITORING_CONFIGURED,
#                  description="Metrics collection configured successfully.",
#                  success=True
#              )
#          else:
#              crud.create_test_status(
#                  db=db,
#                  test_id=test_instance_id,
#                  state=Constants.TestStatus.APPLICATION_MONITORING_CONFIGURED,
#                  description=f"Errors during metrics collection configuration: {errors}",
#                  success=False
#              )
#  else:
#      logging.info(
#          f"No metrics collection info found for test "
#          f"instance: {test_instance_id}"
#      )
#      with get_db() as db:
#          crud.create_test_status(
#              db=db,
#              test_id=test_instance_id,
#              state=Constants.TestStatus.APPLICATION_MONITORING_CONFIGURED,
#              description="No metrics collection info found.",
#              success=True
#          )
#
#
#
#roker.task
#ync def configure_logging_for_test_instance(test_instance_id: int):
#
#  logs_collection_info = None
#
#  # Get Testing Descriptor and obtain metrics collection info
#  with get_db() as db:
#      test_instance = crud.get_test_instances_by_id(db, test_instance_id)
#      
#      logs_collection_info = test_instance["testing_descriptor"].get(
#          "log_collection", None
#      )
#
#  if logs_collection_info:
#      logging.info(
#          "Will configure log collection for test "
#          f"instance: {test_instance_id}"
#      )
#
#      with get_db() as db:
#
#          success, errors = metrics_and_logs.parse_log_collection_info(
#              db, test_instance_id, logs_collection_info
#          )
#
#          if success:
#              crud.create_test_status(
#                  db=db,
#                  test_id=test_instance_id,
#                  state=Constants.TestStatus.APPLICATION_LOGGING_CONFIGURED,
#                  description="Log collection configured successfully.",
#                  success=True
#              )
#          else:
#              crud.create_test_status(
#                  db=db,
#                  test_id=test_instance_id,
#                  state=Constants.TestStatus.APPLICATION_LOGGING_CONFIGURED,
#                  description=f"Errors during log collection configuration: {errors}",
#                  success=False
#              )
#  else:
#      logging.info(
#          f"No log collection info found for test "
#          f"instance: {test_instance_id}"
#      )
#      with get_db() as db:
#          crud.create_test_status(
#              db=db,
#              test_id=test_instance_id,
#              state=Constants.TestStatus.APPLICATION_LOGGING_CONFIGURED,
#              description="No log collection info found.",
#              success=True
#          )
#
#
#