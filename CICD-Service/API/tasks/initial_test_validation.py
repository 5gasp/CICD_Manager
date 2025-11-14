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
async def test(serviceTestParsed: tmf653_schemas.ServiceTest_Create):
    service_test_specification_id = serviceTestParsed.testSpecification.id
    test_instance = None

    # Get Service Test Specification from NODS
    service_test_specification = get_service_test_spec(
        service_test_specification_id
    )
    
    # Render Characteristics
    logging.debug(
        "Will render the characteristics of Service "
        f"Test Specification{service_test_specification_id}"
    )
    characteristics = render_characteristics(serviceTestParsed)
    netapp_id = characteristics["netapp_id"]['value']['value']
    network_service_id = characteristics["network_service_id"]['value']['value']
    testbed_id = characteristics["testbed_id"]['value']['value']
    nods_id = characteristics["NODS_ServiceTest_ID"]['value']['value']

    logging.debug(
        "Service Test Specification {service_test_specification_id} "
        f"Characteristics:\n"
        f"\t- netapp_id: {netapp_id}\n"
        f"\t- network_service_id: {network_service_id}\n"
        f"\t- testbed_id: {testbed_id}\n"
        f"\t- nods_id: {nods_id}\n"
    )

    # Create Test Instance in DB
    logging.debug(
        "Will create a Test Instance for Service "
        f"Test Specification {service_test_specification_id}"
    )
    
    with get_db() as db:
        test_instance = crud.create_test_instance(
            db=db,
            netapp_id=netapp_id,
            network_service_id=network_service_id,
            testbed_id=testbed_id,
            service_test_specification_id=service_test_specification_id,
            nods_id=nods_id,
        )
        logging.info(
            "Created a Test Instance for Service Test Specification"
            f" {service_test_specification_id}: {test_instance.as_dict()}"
        )

    await initial_test_validation.kiq(
        test_instance_id=test_instance.id,
        characteristics=characteristics,
        service_test_specification=service_test_specification,
        testbed_id=testbed_id
    )

    return test_instance

@broker.task
async def initial_test_validation(
    test_instance_id: str,
    characteristics: dict,
    service_test_specification: dict,
    testbed_id: str
):
    # Start by validating the testbed
    # Send the task to the broker.
    task = await validate_testbed.kiq(test_instance_id, testbed_id)
    # Wait for the result.
    result = await task.wait_result(timeout=10)

    success = False
    description = None
    if not result.is_err:
        success, description = result.return_value
        if success:
            logging.debug(description)
            # Create Test Status
            with get_db() as db:
                crud.create_test_status(
                    db=db,
                    test_id=test_instance_id,
                    state=Constants.TestStatus.TESTING_TESTBED_VALIDATED,
                    description=description,
                    success=success
                )
    else:
        success = False
        description = "Error in validating the Testbed. " +\
            f"Error message: {result.error}"

    if not success:
        logging.error(description)
        # Create Test Status
        with get_db() as db:
            crud.create_test_status(
                db=db,
                test_id=test_instance_id,
                state=Constants.TestStatus.TESTING_TESTBED_VALIDATED,
                description=description,
                success=success
            )
            crud.create_test_status(
                db=db,
                test_id=test_instance_id,
                state=Constants.TestStatus.TESTING_PROCESS_ENDED,
                description=description,
                success=success
            )

    # Store Deployment Info in FTP
    await save_deployment_info_in_ftp.kiq(
        test_instance_id=test_instance_id,
        characteristics=characteristics
    )

    # Render Testing Descriptor
    await render_and_validate_testing_descriptor.kiq(
        test_instance_id=test_instance_id,
        characteristics=characteristics,
        service_test_specification=service_test_specification
    )

@broker.task
async def validate_testbed(test_instance_id: int, testbed_id:str):

    success = True
    description = f"Testbed {testbed_id} exists."
    with get_db() as db:
        if crud.get_testbed_by_id(db, testbed_id) is None:
            success = False
            description = f"Testbed {testbed_id} doesn't exist."

    return success, description


@broker.task
async def render_and_validate_testing_descriptor(
    test_instance_id: int,
    characteristics: dict,
    service_test_specification: dict
):
    with get_db() as db:

        # Send the task to the broker.
        task = await get_testing_descriptor.kiq(service_test_specification)
        # Wait for the result.
        result = await task.wait_result(timeout=30)

        descriptors_text = None
        success = True
        description = "Successfully obtained the Testing Descriptor."
        
        if not result.is_err:
            logging.debug(description)
            descriptors_text = result.return_value
        else:
            success = False
            description = "Error in obtaining the Testing Descriptor. " +\
                f"Error message: {result.error}"
            logging.error("Error in getting the Testing Descriptor.")
            logging.error(f"Error type: {type(result.error).__name__}")
            logging.error(f"Error message: {result.error}")
        
        crud.create_test_status(
            db=db,
            test_id=test_instance_id,
            state=Constants.TestStatus.TESTING_DESCRIPTOR_OBTAINED,
            description=description,
            success=success
        )

        if not success:
            return 
        
        # Render Testing Descriptor with Characteristics
        logging.debug("Rendering Testing Descriptor with Characteristics...")
        characteristics_render = test_descriptor_render.CharacteristicsRender(
            characteristics=characteristics,
            testing_descriptor_text=descriptors_text
        )

        rendered_descriptor_yaml = None
        success = True
        description = "Successfully rendered the Testing Descriptor."
        try:
            # Render Testing Descriptors Tags
            rendered_descriptor_yaml = characteristics_render\
                .get_rendered_testing_descritptor()
            logging.info(description)
            logging.debug(f"Rendered Descriptor: \n{rendered_descriptor_yaml}")
        except Exception as e:
            description = "Error in rendering the Testing Descriptor. " +\
                f"Error message: {e}"
            success = False
            logging.error(description)
            
        # Update Testing Descriptor in DB
        test_instance = crud.update_test_instance_testing_descriptor(
            db=db,
            test_id=test_instance_id,
            testing_descriptor=rendered_descriptor_yaml
        )

        # Create Test Status
        crud.create_test_status(
            db=db,
            test_id=test_instance_id,
            state=Constants.TestStatus.TESTING_DESCRIPTOR_RENDERED,
            description=description,
            success=success
        )

        if not success:
            crud.create_test_status(
                db=db,
                test_id=test_instance_id,
                state=Constants.TestStatus.TESTING_PROCESS_ENDED,
                description=description,
                success=success
            )
            return 

        # Send the task to the broker.
        task = await validate_testing_descriptor.kiq(
            test_instance_id=test_instance_id,
            testing_descriptor=rendered_descriptor_yaml
        )

@broker.task
async def validate_testing_descriptor(test_instance_id: int, testing_descriptor: dict):
    success = True
    description = "Testing Descriptor structure is valid."

    # Validate Testing Descriptor Structure
    test_descriptor_validator = Test_Descriptor_Validator(testing_descriptor)
    structural_validation_errors = test_descriptor_validator.validate_structure()
    
    if len(structural_validation_errors) != 0:
        description = "Invalid Testing Descriptor structure. Testing Descriptor"+\
            f"has the following errors: {structural_validation_errors}"
        success = False
        logging.error(description)
    else:
        logging.info(description)
    
    # Create Test Status
    with get_db() as db:
        crud.create_test_status(
            db=db,
            test_id=test_instance_id,
            state=Constants.TestStatus.TESTING_DESCRIPTOR_VALIDATED,
            description=description,
            success=success
        )

        if not success:
            crud.create_test_status(
                db=db,
                test_id=test_instance_id,
                state=Constants.TestStatus.TESTING_PROCESS_ENDED,
                description=description,
                success=success
            )
            return 

@broker.task
async def get_testing_descriptor(service_test_specification: dict):
    
    attachments = {attachment['name']: attachment['url']
        for attachment 
        in service_test_specification['attachment']
    }
    
    try:
        # TODO: Authentication with the NODS should be a decorator
        success, token =  Utils.get_nods_token()

        # Find the testing descriptor filename
        valid_testing_descriptor_filename = [
            attachment_name
            for attachment_name
            in attachments.keys() if "yaml" in attachment_name
        ][0]
        # Get the testing descriptor's URL
        attachment_url = attachments[valid_testing_descriptor_filename]
        # Obtain the testing descriptor
        success, response = Utils.get_serviceTestDescriptor(
            token=token,
            url=attachment_url
        )
        descriptors_text = response.text

        # Validate response
        if not success:
            logging.error("There was an error obtianining the Service Test "\
                f"Descritptor {response}")
            return None

        logging.info("Successfully obtained the Service Test Descriptor.")
        return descriptors_text

    except Exception as e:
        logging.error("There was an exception obtaining the Service Test "\
            f"Descriptor: {e}")
        return None

@broker.task
async def save_deployment_info_in_ftp(test_instance_id: int, characteristics: dict):
    logging.debug("Storing Deployment Information in FTP...")
    testing_artifacts_location = \
        testing_artifacts.store_deployment_information_in_ftp(
            deployment_info=characteristics[
                Constants.TMF_SERVICE_TEST_DEPLOYMENT_INFO_KEY
                ]["value"]["value"],
            nods_id=characteristics["NODS_ServiceTest_ID"]['value']['value']
        )
    with get_db() as db:
        crud.create_testing_artifact(
            db, 
            test_instance_id,
            testing_artifacts_location
        )
    logging.info("Deployment Information stored in FTP at: "
        f"{testing_artifacts_location}"
    )

def get_service_test_spec(service_test_specification_id: str):
    # Authenticate with the NODS
    # TODO: Authentication with the NODS should be a decorator
    success, token =  Utils.get_nods_token()

    # Query the Service Test Specification Endpoint
    try:
        success, response = Utils.get_serviceTestSpecification(
            token=token,
            _id=service_test_specification_id
        )
        if not success:
            logging.error("There was an error obtianining the Service Test "\
                f"Specification: {response}")
            return None

        logging.info(
            "Successfully obtained the Service Test "
            f"Specification (ID: {service_test_specification_id})"
        )
        return response
    except Exception as e:
        logging.error(
            "There was an exception obtaining the Service Test "
            f"Specification (ID: {service_test_specification_id}): {e}"
        )
        return None

def render_characteristics(serviceTestParsed: tmf653_schemas.ServiceTest_Create):
    characteristics = {}
    for characteristic in serviceTestParsed.characteristic:
        characteristics[characteristic.name] = { 
            'id': characteristic.id, 
            'name': characteristic.name, 
            'valueType': characteristic.valueType,
            'value': characteristic.value
        }
    logging.debug("Characteristics Rendered Length:", len(characteristics))
    return characteristics