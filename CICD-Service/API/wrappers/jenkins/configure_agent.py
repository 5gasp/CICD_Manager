
from wrappers.jenkins.wrapper import Jenkins_Wrapper
import sql_app.CRUD.agents as CRUD_Agents
from sql_app import crud
from aux import constants as Constants
import binascii
import logging
import os

# Logger
logging.basicConfig(
    format="%(module)-20s:%(levelname)-15s| %(message)s",
    level=logging.INFO
)


def configure_agent(
        db,
        agent
):
    try:
        # try to create a ci_cd_agent
        # check if the credentials are correct
        jenkins_wrapper = Jenkins_Wrapper()
        ret, message = jenkins_wrapper.connect_to_server(
            agent.url,
            agent.username,
            agent.password
        )
        if not ret:
            return False, "Could not establish a connection with the CI/CD Agent - " + str(message)

        if not crud.get_testbed_by_id(db=db,id=agent.testbed_id):
            return False, f"A testbed with the id {agent.testbed_id} does not exists"

        
        # Create the Jenkins credentials
        
        # LTR-related credentials
        ret, message = jenkins_wrapper.create_credential(
            "ltr_user", Constants.FTP_LTR_USER, "ltr_user")
        if not ret:
            return False, [message], None
                    
        ret, message = jenkins_wrapper.create_credential(
            "ltr_password", Constants.FTP_LTR_PASSWORD, "ltr_password")
        if not ret:
            return False, [message], None
        
        ret, message = jenkins_wrapper.create_credential(
            "ltr_location", Constants.FTP_LTR_URL, "ltr_location")
        if not ret:
            return False, [message], None
        
        # Results Repository-related credentials
        ret, message = jenkins_wrapper.create_credential(
            "results_ftp_user", Constants.FTP_RESULTS_USER, "results_ftp_user")
        if not ret:
            return False, [message], None
        
        ret, message = jenkins_wrapper.create_credential(
            "results_ftp_password", Constants.FTP_RESULTS_PASSWORD, "results_ftp_password")
        if not ret:
            return False, [message], None
        
        ret, message = jenkins_wrapper.create_credential(
            "results_ftp_location", Constants.FTP_RESULTS_URL, "results_ftp_location")
        if not ret:
            return False, [message], None
        
        # Communication Token
        credential_id = "communication_token"
        credential_secret = binascii.b2a_hex(os.urandom(16)).decode('ascii')
        credential_description = "Token used for communication with the CI/CD Manager"
        ret, message = jenkins_wrapper.create_credential(
            credential_id, credential_secret, credential_description)
        if not ret:
            return False, [message], None

        # update communication credential on db
        CRUD_Agents.update_communication_token(db, agent.id, credential_secret)
        
        ret = agent.as_dict_without_password()
        ret["communication_token"] = credential_secret
        
        return True, "Created CI/CD Agent", ret
    except Exception as e:
        logging.error(e)
        return False, [str(e)], None

