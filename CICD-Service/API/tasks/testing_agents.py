from tasks.broker import broker, testing_agents_config
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
import test_helpers.developer_defined as dev_defined_test_helpers
from datetime import datetime, timezone, timedelta
from background_tasks import metrics_and_logs 
from wrappers.jenkins.configure_agent import configure_agent

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
async def provision_testing_agents_for_test_instance(test_instance_id: int):

    test_instance = None
    testing_agents_info = None

    # Get Testing Descriptor and obtain custom testing agents info
    with get_db() as db:
        test_instance = crud.get_test_instances_by_id(db, test_instance_id)
        
        testing_agents_info = test_instance["testing_descriptor"].get(
            "custom_testing_agents", None
        )

    if testing_agents_info:
        logging.info(
            "Will provision custom testing agents for test "
            f"instance: {test_instance_id}"
        )

        testbed_custom_agents = testing_agents_config[test_instance["testbed_id"]]

        service_specs_to_order = []
        for agent in testing_agents_info:
            placement = agent["placement"]
            monitoring = agent["monitoring"]

            # Find matching agent spec in testbed_itav
            for spec in testbed_custom_agents.get(placement, {}).get("agents", []):
                if spec["monitoring"] == monitoring:
                    service_specs_to_order.append(
                        (
                            agent["testing_agent_name"],
                            spec["service_specification_uuid"]
                        )
                    )
                    break 

        logging.info(
            f"Will order the following custom agents {service_specs_to_order}"
        )

        for agent_name, service_spec in service_specs_to_order:
            try:
                # TODO: Authentication with the NODS should be a decorator
                success, token =  Utils.get_nods_token()

                # Get the Service Test Specification from NODS
                service_order_uuid = Utils.order_service(
                    token=token,
                    service_spec_uuid=service_spec
                )
                with get_db() as db:
                    agents_crud.create_custom_ci_cd_agent(
                        db=db,
                        testbed_id=test_instance["testbed_id"],
                        service_order=service_order_uuid,
                        name=agent_name,
                        test_instance_id=test_instance_id,
                        provisioning_started_time=datetime.now(timezone.utc)
                    )

                    crud.create_test_status(
                        db=db,
                        test_id=test_instance_id,
                        state=Constants.TestStatus.CUSTOM_CI_CD_AGENTS_PROVISIONED_STARTED,
                        description=f"Provisionig of Testing Agent {agent_name} for test instance {test_instance_id} started.",
                        success=True
                    )

            except Exception as e:
                description = f"Unable to provisiong Testing Agent {agent_name} for test instance {test_instance_id} - {e}"
                with get_db() as db:
                    crud.create_test_status(
                        db=db,
                        test_id=test_instance_id,
                        state=Constants.TestStatus.CUSTOM_CI_CD_AGENTS_PROVISIONED_STARTED,
                        description=description,
                        success=False
                    )
                    crud.create_test_status(
                        db=db,
                        test_id=test_instance_id,
                        state=Constants.TestStatus.TEST_ENDED,
                        description=description,
                        success=False
                    )
    else:
        logging.info(
            f"No custom testing agents found for test "
            f"instance: {test_instance_id}"
        )
        with get_db() as db:
            description = "No custom testing agents found."
            crud.create_test_status(
                db=db,
                test_id=test_instance_id,
                state=Constants.TestStatus.CUSTOM_CI_CD_AGENTS_PROVISIONED_STARTED,
                description=description,
                success=True
            )
            crud.create_test_status(
                db=db,
                test_id=test_instance_id,
                state=Constants.TestStatus.CUSTOM_CI_CD_AGENTS_PROVISIONED_ENDED,
                description=description,
                success=True
            )


@broker.task
async def confirm_provisioning_of_testing_agents_for_test_instance(test_instance_id: int):
    custom_agents = None

    # Get Testing Descriptor and obtain custom testing agents info
    with get_db() as db:
        custom_agents = agents_crud.get_custom_ci_cd_agents_for_test_instance(
            db=db,
            test_instance_id=test_instance_id
        )
    
    # TODO: Authentication with the NODS should be a decorator
    success, token =  Utils.get_nods_token()

    for custom_agent in custom_agents:
        logging.info(
            f"Will validate if Custom Agent '{custom_agent.name}' "\
            "is already provisioned"
        )

        try:
            # Get the Testing Agents Info NODS
            agent_data = Utils.get_testing_agent_rfs(
                token=token,
                service_order_uuid=custom_agent.service_order
            )

            # If no info was obtained
            if not agent_data:
                # If the agent was deployed more than 10 min ago -> error
                verify_if_agent_provisioning_failed(custom_agent, test_instance_id)

            else:
                url, username, password = agent_data
                description = f"Custom Agent '{custom_agent.name}' has the following " +\
                    f"characteristics: url={url}, username={username}, password={password}"
                logging.info(description)
                
                with get_db() as db:
                    # Update Agent in Database
                    db_custom_agent = agents_crud.update_custom_ci_cd_agent(
                        db=db,
                        test_instance_id=test_instance_id,
                        service_order=custom_agent.service_order,
                        url=url,
                        username=username,
                        password=password,
                        provisioning_finished_time=datetime.now(timezone.utc)
                    )

                    success, errors, data = configure_agent(db, db_custom_agent)

                    if success:
                        # Update Test Status
                        crud.create_test_status(
                            db=db,
                            test_id=test_instance_id,
                            state=Constants.TestStatus.CUSTOM_CI_CD_AGENTS_PROVISIONED_ENDED,
                            description=description,
                            success=success
                        )
                    else:
                        description = "Could not configure credentials in Testing Agent"
                        # Update Test Status
                        crud.create_test_status(
                            db=db,
                            test_id=test_instance_id,
                            state=Constants.TestStatus.CUSTOM_CI_CD_AGENTS_PROVISIONED_ENDED,
                            description=description,
                            success=False
                        )
                        crud.create_test_status(
                            db=db,
                            test_id=test_instance_id,
                            state=Constants.TestStatus.TEST_ENDED,
                            description=description,
                            success=False
                        )

        except Exception as e:
            description = "Could not obtain Testing Agent's Info for 10 minutes - {e}"
            logging.error(description)
            verify_if_agent_provisioning_failed(custom_agent, test_instance_id)


def verify_if_agent_provisioning_failed(custom_agent, test_instance_id):
    # If the agent was deployed more than 10 min ago -> error
    provisioning_started_datetime = custom_agent.provisioning_started_time
    # Make it aware in UTC
    if provisioning_started_datetime.tzinfo is None:
        provisioning_started_datetime = provisioning_started_datetime.replace(tzinfo=timezone.utc)
    
    now_utc = datetime.now(timezone.utc)
    delta = now_utc - provisioning_started_datetime

    # Check if provisioning started more than 10 minutes ago
    if delta > timedelta(minutes=10):
        description = "Could not obtain Testing Agent's Info for 10 minutes"
        logging.info(description)
        
        with get_db() as db:
            crud.create_test_status(
                db=db,
                test_id=test_instance_id,
                state=Constants.TestStatus.CUSTOM_CI_CD_AGENTS_PROVISIONED_ENDED,
                description=description,
                success=False
            )
            crud.create_test_status(
                db=db,
                test_id=test_instance_id,
                state=Constants.TestStatus.TEST_ENDED,
                description=description,
                success=False
            )
