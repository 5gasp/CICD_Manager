# -*- coding: utf-8 -*-
# @Author: Rafael Direito
# @Date:   25-05-2022 11:40:26
# @Email:  rdireito@av.it.pt
# @Last Modified by:   Rafael Direito
# @Last Modified time: 25-05-2022 14:49:27
# @Description: 

import logging
from uuid import UUID
import aux.constants as Constants
import requests
import tarfile
from ftplib import FTP
import os

def load_developer_defined_tests(developer_defined_tests: list[str], 
    attachments: dict, nods_id: str) -> None:
    """Loads the developer defined tests to the CI/CD Manager's FTP Server

    Args:
        developer_defined_tests (list[str]): list of the developer defined tests filepaths
        attachments (dict): list of the serviceTestSpecification attachments
        nods_id (str): id of the serviceTestSpecification in NODS
    """
    # Get the Developer Defined Tests to the local warehouse directory
    for developer_defined_test_name in developer_defined_tests:
        url_to_download = attachments.get(
            f"{developer_defined_test_name}.tar.gz")
        if url_to_download:
            compressed_test_file_location = get_developer_defined_test_to_local_dir(
                developer_defined_test_name,
                url_to_download,
                nods_id
            )
            move_developer_defined_test_to_ftp(compressed_test_file_location)
    



def get_developer_defined_test_to_local_dir( developer_defined_test_name: str, 
    url_to_download: str, nods_id: UUID) -> str:
    """Downloads the developer defined test to the warehouse local directory

    Args:
        developer_defined_test_name (str): name of the developer defined test
        url_to_download (str): url to download the developer defined test
        nods_id (UUID): id of the serviceTestSpecification in NODS

    Returns:
        str: local path to the downloaded developer defined test
    """
    # Get Compressed Test Files
    r = requests.get(
        f"{Constants.NODS_HOST}/tmf-api{url_to_download}",
        allow_redirects=True
    )
    compressed_test_file_location = os.path.join(
        Constants.DEVELOPER_DEFINED_TEST_TEMP_STORAGE_DIR,
        f"{nods_id}-{developer_defined_test_name}.tar.gz"
    )
    open(compressed_test_file_location, 'wb').write(r.content)
    
    return compressed_test_file_location


def move_developer_defined_test_to_ftp(developer_defined_test_path: str) -> None:
    """Copies a developer defined test to the FTP server

    Args:
        developer_defined_test_path (str): local path to the developer defined test
    """
    ftp_url = Constants.FTP_RESULTS_URL.split(":")[0] \
        if ":" in Constants.FTP_RESULTS_URL else Constants.FTP_RESULTS_URL
        
    ftp_session = FTP(
        ftp_url,
        Constants.FTP_RESULTS_USER,
        Constants.FTP_RESULTS_PASSWORD
    )

    # If a directory to store the developer defined tests does not exist, create it
    if Constants.DEVELOPER_DEFINED_TEST_BASE_FTP_DIR not in ftp_session.nlst():
        ftp_session.mkd(Constants.DEVELOPER_DEFINED_TEST_BASE_FTP_DIR)

    ftp_test_full_path = os.path.join(
        Constants.DEVELOPER_DEFINED_TEST_BASE_FTP_DIR,
        os.path.basename(developer_defined_test_path)
    )
    
    if os.path.basename(developer_defined_test_path) in [
        f.split("/")[-1] 
        for f 
        in ftp_session.nlst(Constants.DEVELOPER_DEFINED_TEST_BASE_FTP_DIR)
    ]:
        # delete old version of the test
        ftp_session.delete(ftp_test_full_path)
        
        logging.info("Removed old version of the developer defined test\
        - {developer_defined_test_path}")
        
    # store new version of the tes
    ftp_session.storbinary(
        'STOR ' + ftp_test_full_path, open(developer_defined_test_path, 'rb')
    )
    logging.info("Created new version of the developer defined test - {developer_defined_test_path}")
