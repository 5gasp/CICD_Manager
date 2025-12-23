# -*- coding: utf-8 -*-
# @Author: Rafael Direito
# @Date:   14-10-2021 11:30:17
# @Email:  rdireito@av.it.pt
# @Last Modified by:   Rafael Direito
# @Last Modified time: 26-05-2022 10:29:39
# @Description: 
import os
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

# PIPELINE INFO
BASE_PIPELINE_FILEPATH = os.path.join(currentdir, "pipeline.xml")
BASE_PIPELINE = open(BASE_PIPELINE_FILEPATH).read()

JENKINS_BASE_PIPELINE_SCRIPT = """
pipeline {
    environment {
        CHANGE_NETWORK_QOS = '<CHANGE_NETWORK_QOS>'  
    }
    agent any
    stages {
        stage('Setup environment') {
            environment {
                comm_token = credentials('communication_token')
                test_id = <test_id>
                stage_id = <stage_id>
            }
            steps {
                catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE'){
                    <setup_environment>
                }
            }
            post {
                failure {
                    sh 'curl --retry 5 --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'","stage_id":"\\'"$stage_id"\\'", "success":false, "state": "ENVIRONMENT_SETUP_CI_CD_AGENT"}\\' <ci_cd_manager_url_test_status_url>'
                }
                success {
                    sh 'curl --retry 5 --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'","stage_id":"\\'"$stage_id"\\'", "success":true, "state": "ENVIRONMENT_SETUP_CI_CD_AGENT"}\\'  <ci_cd_manager_url_test_status_url>'
                }
            }
        }
        stage('Obtain all testing artifacts') {
            environment {
                comm_token = credentials('communication_token')
                test_id = <test_id>
                stage_id = <stage_id>
            }
            steps {
                catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE'){
                    <obtain_testing_artifacts>
                }
            }
            post {
                failure {
                    sh 'curl --retry 5 --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'","stage_id":"\\'"$stage_id"\\'", "success":false, "state": "OBTAINED_TESTING_ARTIFACTS_FILES"}\\' <ci_cd_manager_url_test_status_url>'
                }
                success {
                    sh 'curl --retry 5 --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'","stage_id":"\\'"$stage_id"\\'", "success":true, "state": "OBTAINED_TESTING_ARTIFACTS_FILES"}\\'  <ci_cd_manager_url_test_status_url>'
                }
            }
        }
        stage('Obtain Tests') {
            environment {
                <obtain_tests_environment>
                comm_token = credentials('communication_token')
                test_id = <test_id>
                stage_id = <stage_id>
            }
            steps {
                catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE'){
                    <obtain_tests>
                }
            }
            post {
                failure {
                    sh 'curl --retry 5 --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'","stage_id":"\\'"$stage_id"\\'", "success":false, "state": "OBTAINED_TESTS_ON_CI_CD_AGENT"}\\' <ci_cd_manager_url_test_status_url>'
                }
                success {
                    sh 'curl --retry 5 --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'","stage_id":"\\'"$stage_id"\\'", "success":true, "state": "OBTAINED_TESTS_ON_CI_CD_AGENT"}\\'  <ci_cd_manager_url_test_status_url>'
                }
            }
        }
        stage('Configure Network QoS') {
            environment {
                comm_token = credentials('communication_token')
                test_id = <test_id>
                stage_id = <stage_id>
                camara_username = "<camara_username>"
                camara_password = "<camara_password>"
            }
            when {
                expression { env.CHANGE_NETWORK_QOS == 'true' }
            }
            steps {
                script {
                    def basicAuth = sh(
                        script: 'echo -n "$camara_username:$camara_password" | base64',
                        returnStdout: true
                    ).trim()
        
                    def response = sh(
                        script: \"\"\"
                            curl --silent --location \\
                                 --write-out "\\nHTTP_CODE:%{http_code}" \\
                                 --request PATCH '<camara_base_url>/productOrder/<network_qos_profile>/patch' \\
                                 --header 'Content-Type: application/json' \\
                                 --header 'Authorization: Basic ${basicAuth}' \\
                                 --data '{
                                     "administrative_state": "UNLOCKED",
                                     "operational_state": "ENABLED"
                                 }'
                        \"\"\",
                        returnStdout: true
                    ).trim()
        
                    def parts = response.split('HTTP_CODE:')
                    def body = parts[0].trim()
                    def httpCode = parts[1].trim()
                    
                    echo "Response body:"
                    echo body
                    echo "HTTP status: ${httpCode}"
                    
                    if (httpCode != '200') {
                        error("PATCH failed with HTTP ${httpCode}")
                    }
                }
            }
            post {
                failure {
                    sh 'curl --retry 5 --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'","stage_id":"\\'"$stage_id"\\'", "success":false, "state": "CONFIGURED_NETWORK_QOS"}\\' <ci_cd_manager_url_test_status_url>'
                }
                success {
                    sh 'curl --retry 5 --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'","stage_id":"\\'"$stage_id"\\'", "success":true, "state": "CONFIGURED_NETWORK_QOS"}\\'  <ci_cd_manager_url_test_status_url>'
                }
            }
        }
        stage('Perform Tests') {
            environment {
                comm_token = credentials('communication_token')
                test_id = <test_id>
                stage_id = <stage_id>
            }
            steps {
                catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE'){
                    <perform_tests>
                }
            }
            post {
                failure {
                    sh 'curl --retry 5 --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'","stage_id":"\\'"$stage_id"\\'", "success":false, "state": "PERFORMED_TESTS_ON_CI_CD_AGENT"}\\' <ci_cd_manager_url_test_status_url>'
                }
                success {
                    sh 'curl --retry 5 --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'","stage_id":"\\'"$stage_id"\\'", "success":true, "state": "PERFORMED_TESTS_ON_CI_CD_AGENT"}\\'  <ci_cd_manager_url_test_status_url>'
                }
            }
        }
        stage('Publish Results') {
            environment {
                <publish_results_environment>
                comm_token = credentials('communication_token')
                test_id = <test_id>
                stage_id = <stage_id>
            }
            steps {
                catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE'){
                    <publish_results>
                }
            }
            post {
                failure {
                    sh 'curl --retry 5 --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'","stage_id":"\\'"$stage_id"\\'", "success":false, "state": "PUBLISHED_TEST_RESULTS"}\\' <ci_cd_manager_url_test_status_url>'
                }
                success {
                    sh 'curl --retry 5 --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'","stage_id":"\\'"$stage_id"\\'", "success":true, "state": "PUBLISHED_TEST_RESULTS"}\\'  <ci_cd_manager_url_test_status_url>'
                }
            }
        }
        stage('Cleanup environment') {
            environment {
                comm_token = credentials('communication_token')
                test_id = <test_id>
                stage_id = <stage_id>
            }
            steps {
                catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE'){
                    <cleanup_environment>
                }
            }
            post {
                failure {
                    sh 'curl --retry 5 --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'","stage_id":"\\'"$stage_id"\\'", "success":false, "state": "CLEANED_TEST_ENVIRONMENT"}\\' <ci_cd_manager_url_test_status_url>'
                }
                success {
                    sh 'curl --retry 5 --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'","stage_id":"\\'"$stage_id"\\'", "success":true, "state": "CLEANED_TEST_ENVIRONMENT"}\\'  <ci_cd_manager_url_test_status_url>'
                }
            }
        }
        stage('End Testing Process') {
            environment {
                comm_token = credentials('communication_token')
                test_id = <test_id>
                stage_id = <stage_id>
            }
            steps {
                sh 'curl --retry 5 --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'","stage_id":"\\'"$stage_id"\\'", "success":true, "state": "TEST_ENDED"}\\'  <ci_cd_manager_url_test_status_url>'
                sh 'curl --retry 5 --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'","stage_id":"\\'"$stage_id"\\'", "ftp_results_directory":"\\'$JOB_NAME\\'"}\\'  <ci_cd_manager_url_publish_test_results>'
            }
        }
    }
}"""