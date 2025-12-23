from tasks.broker import broker
from sql_app.schemas import TMF653 as tmf653_schemas
import aux.utils as Utils
from aux import startup
from test_helpers import test_descriptor_render, testing_artifacts
from sql_app.database import SessionLocal
from sqlalchemy.orm import Session
from contextlib import contextmanager
from sql_app import crud, models
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
async def process_test_stages(test_instance_id):
    # Get existing test stages and their status
    test_stages_with_status = {}
    with get_db() as db:
        test_stages_with_status = crud.get_test_stages_with_status_for_test_instance(
            db=db,
            test_instance_id=test_instance_id
        )

    all_statuses = {
        status.state
        for statuses
        in test_stages_with_status.values()
        for status in statuses
    }

    is_first_stage_being_executed = models.TestStageStatus.SUBMITTED_PIPELINE_SCRIPT not in all_statuses
    
    # Check if there are test stages being performed
    candidate_test_stages = []
    for test_stage, statuses in test_stages_with_status.items():
        test_stage_states = [s.state for s in statuses]
        if models.TestStageStatus.SUBMITTED_PIPELINE_SCRIPT in test_stage_states\
        and models.TestStageStatus.TEST_ENDED not in test_stage_states:
            # A test stage is being performed and we should wait for it
            # to be completed
            logging.info(
                f"Test Stage {test_stage.id} is still running. Will wait for it to end."
            )
            return
        elif models.TestStageStatus.SUBMITTED_PIPELINE_SCRIPT not in test_stage_states:
            candidate_test_stages.append(test_stage)


    if len(candidate_test_stages) > 0:
        trigger_test_stage(candidate_test_stages.pop(0), is_first_stage_being_executed)


@broker.task
async def check_if_test_stages_ended(test_instance_id):
    # Get existing test stages and their status
    test_stages_with_status = {}
    with get_db() as db:
        test_stages_with_status = crud.get_test_stages_with_status_for_test_instance(
            db=db,
            test_instance_id=test_instance_id
        )

    if all(
        models.TestStageStatus.TEST_ENDED
        in [s.state for s in statuses]
        for statuses in test_stages_with_status.values()
    ):
        # Update Test Status
        crud.create_test_status(
            db=db,
            test_id=test_instance_id,
            state=Constants.TestStatus.TEST_ENDED,
            description=None,
            success=True
        )

def trigger_test_stage(test_stage_db, is_first_stage_being_executed):
    logging.info(f"Will Trigger Test Stage with id '{test_stage_db.id}'")

    testing_agent = None
    test_instance = None
    with get_db() as db:
        # Get testing agent info
        testing_agent = agents_crud.get_ci_cd_node_by_id(
            db=db,
            id=test_stage_db.testing_agent_id
        )
        # Get test instance
        test_instance = crud.get_test_instance(
            db=db,
            test_id=test_stage_db.test_instance_id
        )

    # Define a unique Job Name
    job_name = f"{test_instance.netapp_id}-{test_instance.network_service_id}" +\
        f"-{test_instance.id}-{test_stage_db.id}"
    
    print("Testing Agent:", testing_agent.as_dict())
    print("Job Name:", job_name)

    success, description = send_pipeline_to_jenkins(
        testing_agent,
        test_stage_db,
        job_name
    )

    with get_db() as db:
        if success:
            # Update test stage
            #crud.create_test_stage_status(
            #    db=db,
            #    test_stage_id=test_stage_db.id,
            #    state=models.TestStageStatus.CREATED_PIPELINE_SCRIPT
            #)
            crud.create_test_stage_status(
                db=db,
                test_stage_id=test_stage_db.id,
                state=models.TestStageStatus.SUBMITTED_PIPELINE_SCRIPT
            )

            if is_first_stage_being_executed:
                # Update Test Status
                crud.create_test_status(
                    db=db,
                    test_id=test_instance.id,
                    state=Constants.TestStatus.TESTING_PROCESS_STARTED,
                    description=description,
                    success=True
                )

        else:
            # Update Test Stage
            crud.create_test_stage_status(
                db=db,
                test_stage_id=test_stage_db.id,
                state=models.TestStageStatus.ERROR
            )

            # Update Test Status
            crud.create_test_status(
                db=db,
                test_id=test_instance.id,
                state=Constants.TestStatus.TESTING_PROCESS_STARTED,
                description=description,
                success=False
            )
            crud.create_test_status(
                db=db,
                test_id=test_instance.id,
                state=Constants.TestStatus.TESTING_PROCESS_ENDED,
                description=description,
                success=False
            )

def send_pipeline_to_jenkins(testing_agent, test_stage, job_name):
    try:
        jenkins_wrapper = Jenkins_Wrapper()
        ret, message = jenkins_wrapper.connect_to_server(
            testing_agent.url,
            testing_agent.username,
            testing_agent.password
        )

        if not ret:
            return False, f"Could not authenticate in agent with URL {testing_agent.url} - {message}"
        
        logging.info(f"Successefully accessed agent with URL {testing_agent.url}")

        # Create the Jenkins Script given a pipeline
        jenkins_script = Jenkins_Pipeline_Configuration()\
            .get_jenkins_pipeline_script_from_pipeline_content(test_stage.jenkins_pipeline)

        # Create a new job in Jenkins
        ret, message = jenkins_wrapper.create_new_job(job_name, jenkins_script)
        if not ret:
            description = f"Could not submit pipeline in agent with URL {testing_agent.url} - {message}"
            logging.error(description)
            return False, description
        
        # Trigger Job Execution
        ret, message = jenkins_wrapper.run_job(job_name)
        if not ret:
            description = f"Could not run job in agent with URL {testing_agent.url} - {message}"
            logging.error(description)
            return False, description
        
        # Success
        return True, "Pipeline correctly submitted"
    except Exception as e:
        description = f"Could not send pipeline to agent with URL {testing_agent.url}. Error: {e}"
        logging.error(description)
        return False, description



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
    print("testing_descriptor:", testing_descriptor)
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
                "network_qos_profile": batch.get("network_qos_profile", None),
                "test_cases": batch_test_cases
            }
        )

    # Prepare Jenkins Pipelines
    configured_test_stages = []
    for stage in stages:
        agent = select_agent(test_instance_id, testbed_id, stage["testing_agent"])

        # Create new Testing Stage
        test_stage = create_test_instace_stage(
            test_instance_id=test_instance_id,
            testbed_id=testbed_id,
            testing_agent_id=agent.id,
            test_cases=stage["test_cases"],
            testbed_tests=testbed_tests,
            network_qos_profile=stage["network_qos_profile"]
        )

        if test_stage:
            configured_test_stages.append(test_stage)

            # Register Test Instance Test Cases
            register_test_instace_test_cases(
                test_instance_id=test_instance_id, 
                test_stage_id=test_stage.id,
                test_cases=stage["test_cases"]
            )

    with get_db() as db: 
        if len(configured_test_stages) == len(stages):
            crud.create_test_status(
                db=db,
                test_id=test_instance_id,
                state=Constants.TestStatus.TESTING_PROCESS_STAGES_CONFIGURED,
                description=f"{len(configured_test_stages)} Test Stages were configured",
                success=True
            )
            from tasks.lcm_engine import lcm_engine
            await lcm_engine.kiq()
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


def create_test_instace_stage(test_instance_id, testbed_id, testing_agent_id, test_cases, testbed_tests, network_qos_profile):
    jenkins_wrapper = Jenkins_Wrapper()
    
    try:
        with get_db() as db: 
            # Create Test Stage
            test_stage = crud.create_test_stage(
                db=db,
                test_instance_id=test_instance_id,
                testing_agent_id=testing_agent_id,
                network_qos_profile=network_qos_profile,
                jenkins_pipeline=None,
            )

            # Create jenkins pipeline script
            pipeline_content = jenkins_wrapper.create_jenkins_pipeline(
                executed_tests_info=test_cases,
                available_tests=testbed_tests,
                descriptor_metrics_collection=None, 
                metrics_collection_information=None,
                test_instance_id=test_instance_id,
                test_stage_id=test_stage.id,
                network_qos_profile=network_qos_profile,
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
        logging.error("Error: " + str(e) )
        return None



def register_test_instace_test_cases(test_instance_id, test_stage_id, test_cases):
    with get_db() as db: 
        for test_case in test_cases:
            test_instance_test = crud.create_test_instance_test(
                db=db,
                test_instance_id=test_instance_id,
                test_stage_id=test_stage_id,
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
