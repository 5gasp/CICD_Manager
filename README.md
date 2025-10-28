# 5GASP CI/CD Stack

This repository hosts (i) the components of 5GASP's CI/CD Service (folder `CICD-Service`) and (ii) a Monitoring and Logging stack that can be used for Network Application observability (folder `MonitoringLogging-Stack`).

## CI/CD Service

The CI/CD Service includes various components:
* The CI/CD Manager - The brain of the CI/CD Service
* A PostgreSQL database - to be used by the CI/CD Manager
* The Results Repository (FTP Server) - which persists all test outcomes and results

To deploy the CI/CD Service, you must first provide various information to its service. This can be done by (i) updating the environment variables defined in `CICD-Service/docker/docker-compose.yaml` AND (ii) updating the config file (`CICD-Service/docker/conf_files/config.ini`) for the CI/CD Manager

Regarding the `docker-compose.yaml` file, you must update the `PASV_ADDRESS` variable of the `results_repository`service. This variable should hold the IP on which your results repository will be served. You may also update other configurations, for instance the ports where the services are exposed, or even the database/ftp credentials, but this is not mandatory.

Moving to the `config.ini` configuration file,
* The `RESULTS_FTP` variables should be updated to reflect the credentials and location of the results repository
* The `CI_CD_MANAGER` URL should point to the URL on which the CI/CD Manager is exposed
* The `DB` variables should be configured to reflect the credentials and location of the database
* The `TRVD` host should point to the URL on which the Test Results Visualization Dashboard is exposed. This dashboard is web interface that showcases the outcomes and results of the various testing processes, and is available at [https://github.com/5gasp/CICD-VisualizationDashboard](https://github.com/5gasp/CICD-VisualizationDashboard). Instructions on how to deploy this component can be found in its repository.


When all variables are configured according to your specific deployment, you may deploy the CI/CD Service by running `docker compose up`, within the folder `CICD-Service/docker/`.

## Monitoring and Logging Stack

The Monitoring and Logging Stack includes various components:
* A Prometheus instance - to collect Network Application and Infrastructure metrics
* A Grafana instance - to visualize the collected Network Application and Infrastructure metrics
* A custom Prometheus target update API - this API is triggered by the CI/CD Managaer when a new Network Application is deployed, and we want to collect its metrics. The CI/CD Manager queries this API to trigger the monitoring of a new application
* An ElasticSearch instance - to collect Network Application and Infrastructure logs
* A Kibana instance - to visualize the collected Network Application and Infrastructure logs

To deploy the Monitoring and Logging Stack, you can simply run `docker compose up`, within the folder `MonitoringLogging-Stack`. You may still wish to update some variables in the `docker-file.yaml`, which you are free to do, but it is not mandatory. Various scripts are injected into the previously described components, which automatically integrate Prometheus with Grafana and ElasticSearch with Kibana.

After deploying these services, you will find:
* A Prometheus instance exposed on port 9090
* A Grafana instance, already configured to display the metrics collected by Prometheus, on port 3000
* An ElasticSearch instance ready to consume the logs from applications and infrastructure, on port 9200
* A Kibana instance, already configured to display the logs centralized in ElasticSearch, on port 5601
* A custom Prometheus Target Update API, to register new targets for metrics collection, on port 9091 (this API will be invoked by the CI/CD Manager)



