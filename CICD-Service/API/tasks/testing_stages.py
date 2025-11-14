from tasks.broker import broker
from sql_app.schemas import TMF653 as tmf653_schemas
import aux.utils as Utils
from aux import startup
from test_helpers import test_descriptor_render, testing_artifacts
from sql_app.database import SessionLocal
from sqlalchemy.orm import Session
from contextlib import contextmanager
from sql_app import crud
from sql_app.CRUD import agents as agents_crud
import logging
import aux.constants as Constants
from testing_descriptors_validator.test_descriptor_validator import Test_Descriptor_Validator
import json 
import copy
from wrappers.jenkins.wrapper import Jenkins_Wrapper
from wrappers.jenkins.pipeline_configuration import Jenkins_Pipeline_Configuration


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

@broker.task
async def create_test_stages(test_instance_id, testbed_id, testing_descriptor):

    

    # Get all test cases from testing descriptor
    test_cases = {
        test_case["testcase_id"]: test_case
        for test_case
        in testing_descriptor["testcases"]
    }

    # Get the location of all developer defined test cases
    # Get developer defined tests that existing wihtin the testbed
    dev_defined_test_cases = {}
    testbed_tests = []
    with get_db() as db:
        # Pre-defined test cases for tesbed
        testbed_tests = crud.get_test_info_by_testbed_id(db, testbed_id)
        # Developer Defined
        dev_defined_test_cases = {
            dev_defined.test_case_name : dev_defined.test_case_location
            for dev_defined
            in crud.get_test_instance_dev_defined(
                db=db, 
                test_instance_id=test_instance_id
            )
        }

    stages = []
    # Get all test stages from testing descriptor
    # Each stage will be performed by a individual testing agent
    test_execution_id = 1
    for batch in testing_descriptor["execution"]:
        batch_test_cases = []
        for execution in batch["executions"]:
            for test_case_id in execution["testcase_ids"]:
                batch_test_case = copy.deepcopy(test_cases[test_case_id])

                # Enrich test case
                batch_test_case["test_execution_id"] = test_execution_id
                batch_test_case["is_developer_defined"] = batch_test_case["type"] == "developer-defined"
                batch_test_case["test_instance_id"] = test_instance_id
                batch_test_case["performed_test"] = f"{batch_test_case['name']}-test-id-{batch_test_case['test_execution_id']}"
                batch_test_case["location"] = None

                if batch_test_case["is_developer_defined"]:
                    batch_test_case["performed_test"] = f"dev-defined-{batch_test_case['performed_test']}"
                    batch_test_case["location"] = dev_defined_test_cases[batch_test_case["name"]]

                batch_test_case["full_name"] = batch_test_case["performed_test"]

                batch_test_cases.append(batch_test_case)
                test_execution_id += 1

        stages.append(
            {
                "testing_agent": batch.get("testing_agent", "testbed_default"),
                "test_cases": batch_test_cases
            }
        )
    
    # Prepare Jenkins Pipelines
    configured_test_stages = []
    for stage in stages:
        agent = select_agent(test_instance_id, testbed_id, stage["testing_agent"])

        # Register Test Instance Test Cases
        register_test_instace_test_cases(
            test_instance_id=test_instance_id, 
            test_cases=stage["test_cases"]
        )

        # Create new Testing Stage
        test_stage = create_test_instace_stage(
            test_instance_id=test_instance_id,
            testbed_id=testbed_id,
            testing_agent_id=agent.id,
            test_cases=stage["test_cases"],
            testbed_tests=testbed_tests
        )
        if test_stage:
            configured_test_stages.append(test_stage)

        #print("Script:")
        #print(jenkins_pipeline_config.get_jenkins_pipeline_script_from_pipeline_content(pipeline_content))

    with get_db() as db: 
        if len(configured_test_stages) == len(stages):
            crud.create_test_status(
                db=db,
                test_id=test_instance_id,
                state=Constants.TestStatus.TESTING_PROCESS_STAGES_CONFIGURED,
                description=f"{len(configured_test_stages)} Test Stages were configured",
                success=True
            )
        else:
            description = "Could not create Test Stages"
            # Update Test Status
            crud.create_test_status(
                db=db,
                test_id=test_instance_id,
                state=Constants.TestStatus.TESTING_PROCESS_STAGES_CONFIGURED,
                description=description,
                success=False
            )
            crud.create_test_status(
                db=db,
                test_id=test_instance_id,
                state=Constants.TestStatus.TESTING_PROCESS_ENDED,
                description=description,
                success=False
            )


def create_test_instace_stage(test_instance_id, testbed_id, testing_agent_id, test_cases, testbed_tests):
    jenkins_wrapper = Jenkins_Wrapper()
    try:
        with get_db() as db: 
            # Create Test Stage
            test_stage = crud.create_test_stage(
                db=db,
                test_instance_id=test_instance_id,
                testing_agent_id=testing_agent_id,
                jenkins_pipeline=None
            )

            # Create jenkins pipeline script
            pipeline_content = jenkins_wrapper.create_jenkins_pipeline(
                executed_tests_info=test_cases,
                available_tests=testbed_tests,
                descriptor_metrics_collection=None, 
                metrics_collection_information=None,
                test_instance_id=test_instance_id,
                test_stage_id = test_stage.id,
                testbed_id=testbed_id 
            )

            # Update Test Stage
            test_stage = crud.update_test_stage_with_jenkins_pipeline(
                db=db, 
                test_stage_id=test_stage.id,
                jenkins_pipeline=pipeline_content
            )
            return test_stage
    except Exception as e:
        return None



def register_test_instace_test_cases(test_instance_id, test_cases):
    with get_db() as db: 
        for test_case in test_cases:
            test_instance_test = crud.create_test_instance_test(
                db=db,
                test_instance_id=test_instance_id,
                performed_test=test_case["performed_test"],
                original_test_name= test_case['name'] if \
                    test_case["type"] == "predefined" else "developer-defined",
                description=test_case["description"],
                is_developer_defined=test_case["is_developer_defined"],
                developer_defined_test_filepath=test_case["location"],
            )
            logging.info(
                f"Registered {test_case['type']} test " \
                f"'{test_instance_test.performed_test}' for test instance "\
                f" {test_instance_id}."
            )

def select_agent(test_instance_id, testbed_id, agent_name):
    if agent_name in ["testbed_default", "default"]:
        return select_default_agent(testbed_id)
    return select_custom_agent(test_instance_id, agent_name)

def select_default_agent(testbed_id):
    logging.info(f"Will gather the testbed's default Testing Agent...")
    with get_db() as db:
        testbed_ci_cd_agents = agents_crud.get_default_ci_cd_agents_by_testbed(db, testbed_id)
        # TODO: Improve the selection of the testing agent
        return testbed_ci_cd_agents[0]

def select_custom_agent(test_instance_id, testing_agent_name):
    logging.info(f"Will gather the Custom Testing Agent with the name {testing_agent_name}...")
    with get_db() as db:
        for agent in agents_crud.get_custom_ci_cd_agents_for_test_instance(db, test_instance_id):
            if agent.name == testing_agent_name:
                return agent
