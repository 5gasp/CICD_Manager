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
BASE_PIPELINE = None

JENKINS_BASE_PIPELINE_SCRIPT = """
pipeline {
    agent any
    stages {
        stage('Setup environment') {
            environment {
                comm_token = credentials('communication_token')
                test_id = <test_id>
            }
            steps {
                catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE'){
                    <setup_environment>
                }
            }
            post {
                failure {
                    sh 'curl --retry 5 --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'", "success":false, "state": "ENVIRONMENT_SETUP_CI_CD_AGENT"}\\' <ci_cd_manager_url_test_status_url>'
                }
                success {
                    sh 'curl --retry 5 --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'", "success":true, "state": "ENVIRONMENT_SETUP_CI_CD_AGENT"}\\'  <ci_cd_manager_url_test_status_url>'
                }
            }
        }
        stage('Obtain metrics collection files') {
            environment {
                <obtain_metrics_environment>
                comm_token = credentials('communication_token')
                test_id = <test_id>
            }
            steps {
                catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE'){
                    <obtain_metrics_collection_files>
                }
            }
            post {
                failure {
                    sh 'curl --retry 5 --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'", "success":false, "state": "OBTAINED_METRICS_COLLECTION_FILES"}\\' <ci_cd_manager_url_test_status_url>'
                }
                success {
                    sh 'curl --retry 5 --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'", "success":true, "state": "OBTAINED_METRICS_COLLECTION_FILES"}\\'  <ci_cd_manager_url_test_status_url>'
                }
            }
        }
        stage('Start monitoring') {
            environment {
                comm_token = credentials('communication_token')
                test_id = <test_id>
            }
            steps {
                catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE'){
                    <start_metrics_collection>
                }
            }
            post {
                failure {
                    sh 'curl --retry 5 --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'", "success":false, "state": "STARTED_MONITORING"}\\' <ci_cd_manager_url_test_status_url>'
                }
                success {
                    sh 'curl --retry 5 --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'", "success":true, "state": "STARTED_MONITORING"}\\'  <ci_cd_manager_url_test_status_url>'
                }
            }
        }
        stage('Obtain Tests') {
            environment {
                <obtain_tests_environment>
                comm_token = credentials('communication_token')
                test_id = <test_id>
            }
            steps {
                catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE'){
                    <obtain_tests>
                }
            }
            post {
                failure {
                    sh 'curl --retry 5 --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'", "success":false, "state": "OBTAINED_TESTS_ON_CI_CD_AGENT"}\\' <ci_cd_manager_url_test_status_url>'
                }
                success {
                    sh 'curl --retry 5 --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'", "success":true, "state": "OBTAINED_TESTS_ON_CI_CD_AGENT"}\\'  <ci_cd_manager_url_test_status_url>'
                }
            }
        }
        stage('Perform Tests') {
            environment {
                comm_token = credentials('communication_token')
                test_id = <test_id>
            }
            steps {
                catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE'){
                    <perform_tests>
                }
            }
            post {
                failure {
                    sh 'curl --retry 5 --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'", "success":false, "state": "PERFORMED_TESTS_ON_CI_CD_AGENT"}\\' <ci_cd_manager_url_test_status_url>'
                }
                success {
                    sh 'curl --retry 5 --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'", "success":true, "state": "PERFORMED_TESTS_ON_CI_CD_AGENT"}\\'  <ci_cd_manager_url_test_status_url>'
                }
            }
        }
        stage('End monitoring') {
            environment {
                comm_token = credentials('communication_token')
                test_id = <test_id>
            }
            steps {
                catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE'){
                    <end_metrics_collection>
                }
                
            }
            post {
                failure {
                    sh 'curl --retry 5 --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'", "success":false, "state": "ENDED_MONITORING"}\\' <ci_cd_manager_url_test_status_url>'
                }
                success {
                    sh 'curl --retry 5 --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'", "success":true, "state": "ENDED_MONITORING"}\\'  <ci_cd_manager_url_test_status_url>'
                }
            }
        }
        stage('Publish Results') {
            environment {
                <publish_results_environment>
                comm_token = credentials('communication_token')
                test_id = <test_id>
            }
            steps {
                catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE'){
                    <publish_results>
                }
            }
            post {
                failure {
                    sh 'curl --retry 5 --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'", "success":false, "state": "PUBLISHED_TEST_RESULTS"}\\' <ci_cd_manager_url_test_status_url>'
                }
                success {
                    sh 'curl --retry 5 --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'", "success":true, "state": "PUBLISHED_TEST_RESULTS"}\\'  <ci_cd_manager_url_test_status_url>'
                }
            }
        }
        stage('Cleanup environment') {
            environment {
                comm_token = credentials('communication_token')
                test_id = <test_id>
            }
            steps {
                catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE'){
                    <cleanup_environment>
                }
            }
            post {
                failure {
                    sh 'curl --retry 5 --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'", "success":false, "state": "CLEANED_TEST_ENVIRONMENT"}\\' <ci_cd_manager_url_test_status_url>'
                }
                success {
                    sh 'curl --retry 5 --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'", "success":true, "state": "CLEANED_TEST_ENVIRONMENT"}\\'  <ci_cd_manager_url_test_status_url>'
                }
            }
        }
        stage('End Testing Process') {
            environment {
                comm_token = credentials('communication_token')
                test_id = <test_id>
            }
            steps {
                sh 'curl --retry 5 --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'", "success":true, "state": "TEST_ENDED"}\\'  <ci_cd_manager_url_test_status_url>'
                sh 'curl --retry 5 --header "Content-Type: application/json" --request POST --data \\'{"communication_token":"\\'"$comm_token"\\'","test_id":"\\'"$test_id"\\'", "ftp_results_directory":"\\'$JOB_NAME\\'"}\\'  <ci_cd_manager_url_publish_test_results>'
            }
        }
    }
}"""