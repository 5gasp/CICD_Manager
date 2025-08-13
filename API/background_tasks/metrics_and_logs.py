from aux import constants as Constants
import logging
import requests
import json
import random
import string
from sql_app import crud

#Constants.PROMETHEUS_TARGET_UPDATE_API = "http://10.255.28.74:9091/targets"
#Constants.GRAFANA_DATASOURCE_UID = 'prometheus-main'
#Constants.GRAFANA_USERNAME = "admin"
#Constants.GRAFANA_PASSWORD = "admin"
#Constants.GRAFANA_IP_OR_DOMAIN = "10.255.28.74"
#Constants.GRAFANA_PORT = 3000
#Constants.DASHBOARD_UID_LENGTH = 9
#Constants.KIBANA_USERNAME = "elastic"
#Constants.KIBANA_PASSWORD = "password"
#Constants.KIBANA_IP_OR_DOMAIN = "10.255.28.74"
#Constants.KIBANA_PORT = 5601
# Logger
logging.basicConfig(
    format="%(module)-20s:%(levelname)-15s| %(message)s",
    level=logging.INFO
)


def parse_log_collection_info(db, test_id, log_collection_info):
    # TODO: Implement additional logic to handle metrics collection
    # For now only supports prometheus (and badly - just to get results for a paper)
    # This code is fucking trash, but it works for the paper
    for log_collection_obj in log_collection_info:
        agent_name = log_collection_obj["test_agent_name"]
        viewer = log_collection_obj["viewer"]
        if viewer == "kibana":
            kibana_url = f"http://{Constants.KIBANA_IP_OR_DOMAIN}:" +\
                f"{Constants.KIBANA_PORT}/app/logs/stream?logFilter=" +\
                f"(expression:'test_agent_name:\"{agent_name}\"'," +\
                "kind:kuery)&logPosition=(streamLive:!t)"
            logging.info(
                f"Kibana URL for agent {agent_name}: {kibana_url}"
            )
            crud.create_logs_dasboard(
                db, test_id, kibana_url, Constants.KIBANA_USERNAME,
                Constants.KIBANA_PASSWORD
            )
        
def parse_metrics_collection_info(db, test_id, metrics_collection_info):
    # TODO: Implement additional logic to handle metrics collection
    # For now only supports prometheus (and badly - just to get results for a paper)
    # This code is fucking trash, but it works for the paper
    for metrics_collection_obj in metrics_collection_info:
        targets = []
        job_name = metrics_collection_obj["job_name"]
        viewer = metrics_collection_obj["viewer"]
        for metric_collection in metrics_collection_obj["metrics_collection"]:
            if metric_collection['type'] == 'prometheus':
                targets.append(metric_collection['collection_endpoint'])
        try:
            if register_prometheus_targets(job_name, targets):
                if viewer["type"] == "grafana":
                    grafana_url = create_grafana_dashboard(
                        job_name, viewer
                    )
                    logging.info(
                        f"Grafana dashboard created successfully: {grafana_url}"
                    )
                    crud.create_metrics_dasboard(
                        db, test_id, grafana_url, Constants.GRAFANA_USERNAME,
                        Constants.GRAFANA_PASSWORD
                    )
        
        except Exception as e:
            logging.error(
                f"Error while processing metrics collection for test {test_id}: {str(e)}"
            )
            continue
                
        
def register_prometheus_targets(job_name, targets):
    logging.info("Starting to register Prometheus Targets...")
    try:
        payload = {
            "job_name": job_name,
            "targets": targets
        }
        
        headers = {'Content-Type': 'application/json'}
        response = requests.request(
            "POST",
            Constants.PROMETHEUS_TARGET_UPDATE_API,
            headers=headers,
            data=json.dumps(payload)
        )
        response.raise_for_status()
        logging.info(f"Status Code: {response.status_code}")
        logging.info(f"Response: {response.text}")
        logging.info(
            f"Successfully registered Prometheus targets for job: {job_name}"
        )
        return True
    except Exception as e:
        logging.error(f"Error registering Prometheus targets: {str(e)}")
        return False

def create_grafana_dashboard(job_name, viewer):
    # This is hardcoded - just for a paper
    dashboard_src = viewer["dashboard_src"]
    dashboard_name = viewer["name_for_dashboard"]
    dashboard_uid = ''.join(random.choice(string.ascii_letters) for _ \
        in range(int(Constants.DASHBOARD_UID_LENGTH)))

    # Fetch JSON from URL
    response = requests.get(dashboard_src)
    response.raise_for_status()  # raise error if the request failed
    data = response.json() 
    
    # Change the UID and title of the dashboard
    data['uid'] = dashboard_uid
    data['title'] = dashboard_name
    # Update the templating section with job and datasource templates
    data["templating"]["list"][0] = render_data_source_template()
    data["templating"]["list"][1] = render_job_template(job_name)   
    # Prepare the output data structure
    output_data = {
        "dashboard": data,
        "folderUid":"",
        "inputs": [
            {
                "name": "DS_PROMETHEUS",
                "type": "datasource",
                "pluginId": "prometheus",
                "value": Constants.GRAFANA_DATASOURCE_UID
            }
        ]     
    }
    logging.info(
        f"Will now submit the dashboard named {data['title']} to Grafana..."
    )
        
    grafana_url = \
        f"http://{Constants.GRAFANA_USERNAME}:{Constants.GRAFANA_PASSWORD}" +\
        f"@{Constants.GRAFANA_IP_OR_DOMAIN}:{Constants.GRAFANA_PORT}" +\
        "/api/dashboards/import"
    
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request(
        "POST",
        grafana_url,
        headers=headers,
        data=json.dumps(output_data)
    )
    
    # Check status code and response
    response.raise_for_status()
    
    logging.info("Dashboard imported successfully!")
    logging.info("Response from Grafana:")
    logging.info(response.json())
    response_data = response.json()
    return f"http://{Constants.GRAFANA_IP_OR_DOMAIN}:{Constants.GRAFANA_PORT}" +\
        response_data["importedUrl"]


def render_job_template(job_name):
    return {
        "current": {
            "text": job_name,
            "value": job_name
        },
        "description": "",
        "hide": 2,
        "label": "Job",
        "name": "job",
        "query": job_name,
        "skipUrlSync": True,
        "type": "constant"
    }
    
def render_data_source_template():
    return {
        "current": {
            "text": "Prometheus",
            "value": Constants.GRAFANA_DATASOURCE_UID
        },
        "hide": 2,
        "label": "Datasource",
        "name": "DS_PROMETHEUS",
        "refresh": 1,
        "regex": "",
        "skipUrlSync": True,
        "type": "constant"
    }