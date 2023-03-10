import aux.utils as Utils
import logging
from uuid import UUID
import aux.constants as Constants
import ftputil
import os
import re
import json
import yaml

class DeploymentInfoTemplateTag:
    
    nsi_id = None
    vnfi_id = None
    value = None
    
    
    def __init__(self, original_template, template):
        self.original_template = original_template
        self.template = template
        self.path = template.split("|")

class CharacteristicsRender:
    
    deployment_templates = None
    rendered_testing_descritptor = None
    
    def __init__(self, characteristics, testing_descriptor_text):
        self.characteristics = characteristics
        self.testing_descriptor_text = testing_descriptor_text
        
    @property
    def deployment_information(self):
        try:
            deployment_information = self.characteristics[
                Constants.TMF_SERVICE_TEST_DEPLOYMENT_INFO_KEY
            ]["value"]["value"]
            return deployment_information
        except Exception as e:
            raise Exception(f"Impossible to obtain the deployment "\
                    "information from the serviceTest payload. Are you sure "\
                    "the deployment information is comprised in a "\
                    "characteristic named 'deployment_information'? "\
                    f"Exception: {e}"
                )        

    
    def get_rendered_testing_descritptor(self):
        
        # If the descriptor was parsed, don't parse it again
        if self.rendered_testing_descritptor is not None:
            return self.rendered_testing_descritptor
        
        # 1. Render regular templates
        self._render_regular_characteristics()
        
        # 2. Render deployment info templates
        self._render_deployment_info()
        
        # Parse to YAML
        self.rendered_testing_descritptor = yaml.safe_load(
            self.testing_descriptor_text
        )
        
        return self.rendered_testing_descritptor
    
    
    def _render_regular_characteristics(self):
        for characteristic_name in self.characteristics.keys():
            value = self.characteristics[characteristic_name]["value"]["value"]
            if not isinstance(value, dict):
                self.testing_descriptor_text = self.testing_descriptor_text\
                    .replace(
                        "{{" + characteristic_name + "}}",
                        value
                    )
 
        
    def _render_deployment_info(self):

        self._gather_deployment_info_templates()

        for template in self.deployment_templates:
            # Todo Optimize latter
            # get NS Record ID
            for artifact, deployed_artifact in self.deployment_information.items():
                if "nsd" in deployed_artifact\
                and deployed_artifact["nsd"]["id"] == template.path[0]:
                    template.nsi_id = deployed_artifact["id"]
            
            # If VNF
            if True:
                 # get VNF Record ID
                self._render_vnf_deployment_info(template)
            # If CNF
            elif False:
                pass

            if template.value is None:
                raise Exception("Impossible to obtain the value referenced "\
                    f"by the template {template.original_template}")

        # Update Testing Descriptor 
        self._update_testing_descriptor()


    def _update_testing_descriptor(self):
        logging.info("Rendering the Testing Descriptor according to the "\
            "deployment tamplate values")
        
        for deployment_template in self.deployment_templates:
            self.testing_descriptor_text = self.testing_descriptor_text\
                .replace(
                    f"{deployment_template.original_template}",
                    f"{deployment_template.value}"
                )
    
        
    def _render_vnf_deployment_info(self, template):
        for artifact, deployed_artifact in self.deployment_information.items():
            if "nsr-id-ref" in deployed_artifact\
            and deployed_artifact["nsr-id-ref"] == template.nsi_id\
            and deployed_artifact["member-vnf-index-ref"] == template.path[1]:
                # Get VNF Instance Record ID
                template.vnfi_id = deployed_artifact["_id"]
                # Get template values from interfaces
                for vdur in deployed_artifact["vdur"]:
                    for interface in vdur["interfaces"]:
                        if "external-connection-point-ref" in interface\
                        and interface["external-connection-point-ref"]\
                        == template.path[2]:
                            template.value = interface[template.path[3]]
                            logging.info(f"The template "\
                                f"{template.original_template} has the value "\
                                f"{template.value}")
                        break
                    if template.value is not None: break
            if template.value is not None: break
       
                
    
    
    def _gather_deployment_info_templates(self):
        template_pattern = re.compile(r"value:\s*({{(deployment_info\|.*)}})")
        
        templates = {}
        for match in template_pattern.finditer(self.testing_descriptor_text):
            templates[match.group(1)] = match.group(2).replace(
                "deployment_info|", ""
            )
            
        logging.info("The testing descriptor has the following deployment "\
            f"templates: {', '.join(list(templates.keys()))}")
        
        self.deployment_templates = [
            DeploymentInfoTemplateTag(k,v) 
            for k,v 
            in templates.items()
        ]
    
    

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
            
            return f"{Constants.TESTING_ARTIFACTS_FTP_ROOT_PATH}/"\
                f"{nods_id}"

    except Exception as e:
        raise Exception(f"Impossible to store the deployment information "\
                f"in the FTP Server. Exception: {e}"
            )
        