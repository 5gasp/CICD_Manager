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

@broker.task
async def configure_monitoring_for_test_instance(test_instance_id: int):

    metrics_collection_info = None

    # Get Testing Descriptor and obtain metrics collection info
    with get_db() as db:
        test_instance = crud.get_test_instances_by_id(db, test_instance_id)
        
        metrics_collection_info = test_instance["testing_descriptor"].get(
            "metrics_collection", None
        )

    if metrics_collection_info:
        logging.info(
            "Will configure metrics collection for test "
            f"instance: {test_instance_id}"
        )

        with get_db() as db:

            success, errors = metrics_and_logs.parse_metrics_collection_info(
                db, test_instance_id, metrics_collection_info
            )

            if success:
                crud.create_test_status(
                    db=db,
                    test_id=test_instance_id,
                    state=Constants.TestStatus.APPLICATION_MONITORING_CONFIGURED,
                    description="Metrics collection configured successfully.",
                    success=True
                )
            else:
                crud.create_test_status(
                    db=db,
                    test_id=test_instance_id,
                    state=Constants.TestStatus.APPLICATION_MONITORING_CONFIGURED,
                    description=f"Errors during metrics collection configuration: {errors}",
                    success=False
                )
    else:
        logging.info(
            f"No metrics collection info found for test "
            f"instance: {test_instance_id}"
        )
        with get_db() as db:
            crud.create_test_status(
                db=db,
                test_id=test_instance_id,
                state=Constants.TestStatus.APPLICATION_MONITORING_CONFIGURED,
                description="No metrics collection info found.",
                success=True
            )



@broker.task
async def configure_logging_for_test_instance(test_instance_id: int):

    logs_collection_info = None

    # Get Testing Descriptor and obtain metrics collection info
    with get_db() as db:
        test_instance = crud.get_test_instances_by_id(db, test_instance_id)
        
        logs_collection_info = test_instance["testing_descriptor"].get(
            "log_collection", None
        )

    if logs_collection_info:
        logging.info(
            "Will configure log collection for test "
            f"instance: {test_instance_id}"
        )

        with get_db() as db:

            success, errors = metrics_and_logs.parse_log_collection_info(
                db, test_instance_id, logs_collection_info
            )

            if success:
                crud.create_test_status(
                    db=db,
                    test_id=test_instance_id,
                    state=Constants.TestStatus.APPLICATION_LOGGING_CONFIGURED,
                    description="Log collection configured successfully.",
                    success=True
                )
            else:
                crud.create_test_status(
                    db=db,
                    test_id=test_instance_id,
                    state=Constants.TestStatus.APPLICATION_LOGGING_CONFIGURED,
                    description=f"Errors during log collection configuration: {errors}",
                    success=False
                )
    else:
        logging.info(
            f"No log collection info found for test "
            f"instance: {test_instance_id}"
        )
        with get_db() as db:
            crud.create_test_status(
                db=db,
                test_id=test_instance_id,
                state=Constants.TestStatus.APPLICATION_LOGGING_CONFIGURED,
                description="No log collection info found.",
                success=True
            )


