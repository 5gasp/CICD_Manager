import aux.utils as Utils
import logging
from uuid import UUID
import aux.constants as Constants
import ftputil
import os
import re
import json
import yaml
import urllib
import shutil

def store_deployment_information_in_ftp(deployment_info, nods_id):
    try:
        # Check if base dir exists
        ftp_host = Constants.FTP_RESULTS_URL.split(":")[0]
        with ftputil.FTPHost(ftp_host, Constants.FTP_RESULTS_USER, 
                             Constants.FTP_RESULTS_PASSWORD) as ftp_host:

            # If the root directory does not exist, create it
            if not ftp_host.path.isdir(
                    Constants.TESTING_ARTIFACTS_FTP_ROOT_PATH
                ):
                logging.info("Root directory for the testing artifacts "\
                    "does not exist. Creating it...")
            
                ftp_host.mkdir(Constants.TESTING_ARTIFACTS_FTP_ROOT_PATH)
                
                logging.info("Testing artifacts directory was created!")
                
            # Create a directory to store all testing artifacts of this test 
            # instance
            logging.info("Creating directory to store all testing artifacts "\
                "of this test instance...")
            
            ftp_host.chdir(Constants.TESTING_ARTIFACTS_FTP_ROOT_PATH)
            
            if not ftp_host.path.isdir(nods_id):
                ftp_host.mkdir(nods_id)
            
            logging.info("Created directory to store all testing artifacts "\
                "of this test instance: "\
                f"{Constants.TESTING_ARTIFACTS_FTP_ROOT_PATH}/{nods_id}."
            )
            
            # Store file locally
            logging.info("Locally storing deployment information...")
            
            # if local directory does not exist
            local_dir_path = os.path.join(
                Constants.TESTING_ARTIFACTS_FTP_TEMP_STORAGE_DIR,
                nods_id
            )
            if not os.path.isdir(local_dir_path):
                os.mkdir(local_dir_path)
                
            # locally store the deployment information
            deployment_info_tmp_location = os.path.join(
                Constants.TESTING_ARTIFACTS_FTP_TEMP_STORAGE_DIR,
                nods_id,
                Constants.DEPLOYMENT_INFO_FNAME
            )
            
            f = open(deployment_info_tmp_location, 'w')
            f.write(json.dumps(deployment_info, indent = 4))
            f.close()
            
            logging.info("Deployment information locally stored at: "\
                f"{Constants.TESTING_ARTIFACTS_FTP_TEMP_STORAGE_DIR}/{nods_id}/"
                f"{Constants.DEPLOYMENT_INFO_FNAME}"
            )
            
            # Move deployment info to FTP
            logging.info("Uploading deployment information to FTP ...")
            
            ftp_host.upload(
                source=deployment_info_tmp_location,
                target=f"{Constants.TESTING_ARTIFACTS_FTP_ROOT_PATH}/"\
                    f"{nods_id}/{Constants.DEPLOYMENT_INFO_FNAME}"
            )
            
            logging.info("Deployment information to FTP. Location: "\
                f"{Constants.TESTING_ARTIFACTS_FTP_ROOT_PATH}/{nods_id}/"
                f"{Constants.DEPLOYMENT_INFO_FNAME}"
            )
            
            # Remove local copy
            shutil.rmtree(os.path.join(
                Constants.TESTING_ARTIFACTS_FTP_TEMP_STORAGE_DIR,
                nods_id)
            )
            
            
            
            
            return f"{Constants.TESTING_ARTIFACTS_FTP_ROOT_PATH}/"\
                f"{nods_id}"

    except Exception as e:
        raise Exception(f"Impossible to store the deployment information "\
                f"in the FTP Server. Exception: {e}"
            )


def get_testing_artifact_from_ftp(ftp_base_path, artifact):
    try:
        ftp_location = Constants.FTP_RESULTS_URL.split(":")[0] \
            if ":" in Constants.FTP_RESULTS_URL else Constants.FTP_RESULTS_URL
            
        url = f"ftp://{Constants.FTP_RESULTS_USER}:{Constants.FTP_RESULTS_PASSWORD}" \
            f"@{ftp_location}/{ftp_base_path[1:]}/{artifact}"

        # Todo -> Fix this mess later
        mime_type = None
        if artifact.endswith(".json"):
            mime_type = "application/json"
        elif artifact.endswith(".gzip"):
            mime_type = "application/tar+gzip"
        else:
            mime_type = "text/plain"
            
        logging.info(f"Will Obtain the following testing artifact: {ftp_location}"\
            f"/{artifact}'. MIMe type: {mime_type}")
            
        # Read File content
        r = urllib.request.urlopen(url)
        testing_artifact_content = r.read()
        
        return testing_artifact_content, mime_type
        
    except Exception as e:
        raise Exception(f"Impossible to obtain the testing artifact from the "\
                f"FTP Server. Exception: {e}"
            )
        