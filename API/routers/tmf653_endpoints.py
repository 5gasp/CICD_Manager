#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Author: Rafael Direito (rdireito@av.it.pt)
# Date: 1st july 2021
# Last Update: 12th july 2021

# Description:
# Constains all the endpoints related to the CI/CD Agents

# generic imports
from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session
from sql_app.database import SessionLocal
from sqlalchemy.orm import Session
from sql_app import crud
from sql_app.schemas import TMF653 as tmf653_schemas
from typing import List
import logging
import inspect
import sys
import os
import aux.constants as Constants
from fastapi.responses import FileResponse
import requests
import yaml


# import from parent directory
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

# custom imports
import aux.utils as Utils
router = APIRouter()

# Logger
logging.basicConfig(
    format="%(module)-20s:%(levelname)-15s| %(message)s",
    level=logging.INFO
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post(
    "/tmf-api/serviceTestManagement/v4/serviceTest", 
)
def create_service_test(serviceTest: tmf653_schemas.ServiceTest_Create , db: Session = Depends(get_db)):
    # Get Service Test Characteristics
    characteristics = []
    for characteristic in serviceTest.characteristic:
        characteristics.append({
            'id': characteristic.id, 
            'name': characteristic.name, 
            'valueType': characteristic.valueType,
            'value': characteristic.value
        })

    # Get the Service Test Specification Id
    service_test_specification_id = serviceTest.testSpecification.id
    service_test_specification_href = serviceTest.testSpecification.href

    # Query the Service Test Specification Endpoint
    response = requests.get(service_test_specification_href)
    response_dic = response.json()

    # Get the attachment (testing descriptor)
    attachment_url = response_dic['data']['attachment'][0]["url"]
    response = requests.get(attachment_url)
    descriptors_text = response.text
    
    # Render Descriptor
    for characteristic in characteristics:
        descriptors_text = descriptors_text.replace(f"<{characteristic['id']}>", characteristic['value'])
    rendered_descriptor = yaml.safe_load(descriptors_text)

    # @Todo - change the response. This is just to preview the file via postman 
    return Utils.create_response(success=True, message="Descriptor's Augmentation was Successful", data=rendered_descriptor)


# SIMULATE THE NODS !!!
@router.get(
    "/tmf-api/serviceTestManagement/v4/serviceTestSpecification/{serviceTestSpecificationId}", 
)
def create_service_test(serviceTestSpecificationId, db: Session = Depends(get_db)):
    # Dummy Response
    response_data = {
        "id": "string",
        "href": "string",
        "description": "string",
        "isBundle": True,
        "lastUpdate": "2021-11-08T14:43:44.186Z",
        "lifecycleStatus": "string",
        "name": "string",
        "version": "string",
        # IMPORTANT --------------------------- * 
        "attachment": [
            {
            "id": "base_testing_descriptor",
            "href": f"{Constants.CI_CD_MANAGER_URL}/Attachment/base_testing_descriptor",
            "attachmentType": "yaml",
            "content": "---",
            "description": "Testing Descriptor Before Rendering",
            "mimeType": "string",
            "name": "base_testing_descriptor.yaml",
            "url": f"{Constants.CI_CD_MANAGER_URL}/Content/base_testing_descriptor",
            "size": {
                "amount": 1,
                "units": "string"
            },
            "validFor": {
                "endDateTime": "1985-04-12T23:20:50.52Z",
                "startDateTime": "1985-04-12T23:20:50.52Z"
            },
            "@baseType": "string",
            "@schemaLocation": "string",
            "@type": "string",
            "@referredType": "string"
            }
        ],
        # END OF IMPORTANT -------------------- * 
        "constraint": [
            {
            "id": "string",
            "href": "string",
            "name": "string",
            "version": "string",
            "@baseType": "string",
            "@schemaLocation": "string",
            "@type": "string",
            "@referredType": "string"
            }
        ],
        "entitySpecRelationship": [
            {
            "id": "string",
            "href": "string",
            "name": "string",
            "relationshipType": "string",
            "role": "string",
            "associationSpec": {
                "id": "string",
                "href": "string",
                "name": "string",
                "@baseType": "string",
                "@schemaLocation": "string",
                "@type": "string",
                "@referredType": "string"
            },
            "validFor": {
                "endDateTime": "1985-04-12T23:20:50.52Z",
                "startDateTime": "1985-04-12T23:20:50.52Z"
            },
            "@baseType": "string",
            "@schemaLocation": "string",
            "@type": "string",
            "@referredType": "string"
            }
        ],
        "relatedParty": [
            {
            "id": "string",
            "href": "string",
            "name": "string",
            "role": "string",
            "@baseType": "string",
            "@schemaLocation": "string",
            "@type": "string",
            "@referredType": "string"
            }
        ],
        "relatedServiceSpecification": [
            {
            "id": "string",
            "href": "string",
            "name": "string",
            "version": "string",
            "@baseType": "string",
            "@schemaLocation": "string",
            "@type": "string",
            "@referredType": "string"
            }
        ],
        "serviceTestSpecRelationship": [
            {
            "id": "string",
            "href": "string",
            "name": "string",
            "relationshipType": "string",
            "role": "string",
            "validFor": {
                "endDateTime": "1985-04-12T23:20:50.52Z",
                "startDateTime": "1985-04-12T23:20:50.52Z"
            },
            "@baseType": "string",
            "@schemaLocation": "string",
            "@type": "string",
            "@referredType": "string"
            }
        ],
        "specCharacteristic": [
            {
            "id": "string",
            "configurable": True,
            "description": "string",
            "extensible": True,
            "isUnique": True,
            "maxCardinality": 0,
            "minCardinality": 0,
            "name": "string",
            "regex": "string",
            "valueType": "string",
            "charSpecRelationship": [
                {
                "characteristicSpecificationId": "string",
                "name": "string",
                "parentSpecificationHref": "string",
                "parentSpecificationId": "string",
                "relationshipType": "string",
                "validFor": {
                    "endDateTime": "1985-04-12T23:20:50.52Z",
                    "startDateTime": "1985-04-12T23:20:50.52Z"
                },
                "@baseType": "string",
                "@schemaLocation": "string",
                "@type": "string"
                }
            ],
            "characteristicValueSpecification": [
                {
                "isDefault": True,
                "rangeInterval": "string",
                "regex": "string",
                "unitOfMeasure": "string",
                "valueFrom": 0,
                "valueTo": 0,
                "valueType": "string",
                "validFor": {
                    "endDateTime": "1985-04-12T23:20:50.52Z",
                    "startDateTime": "1985-04-12T23:20:50.52Z"
                },
                "value": "string",
                "@baseType": "string",
                "@schemaLocation": "string",
                "@type": "string"
                }
            ],
            "validFor": {
                "endDateTime": "1985-04-12T23:20:50.52Z",
                "startDateTime": "1985-04-12T23:20:50.52Z"
            },
            "@baseType": "string",
            "@schemaLocation": "string",
            "@type": "string",
            "@valueSchemaLocation": "string"
            }
        ],
        "targetEntitySchema": {
            "@schemaLocation": "string",
            "@type": "string"
        },
        "testMeasureDefinition": [
            {
            "captureFrequency": "string",
            "captureMethod": "string",
            "metricDescription": "string",
            "metricHref": "string",
            "metricName": "string",
            "name": "string",
            "unitOfMeasure": "string",
            "valueType": "string",
            "capturePeriod": {
                "amount": 0,
                "units": "string"
            },
            "thresholdRule": [
                {
                "conformanceComparatorExact": True,
                "conformanceComparatorLower": "string",
                "conformanceComparatorUpper": "string",
                "conformanceTargetExact": "string",
                "conformanceTargetLower": "string",
                "conformanceTargetUpper": "string",
                "description": "string",
                "name": "string",
                "numberOfAllowedCrossing": 0,
                "thresholdRuleSeverity": "string",
                "consequence": [
                    {
                    "description": "string",
                    "name": "string",
                    "prescribeAction": "string",
                    "repeatAction": True,
                    "validFor": {
                        "endDateTime": "1985-04-12T23:20:50.52Z",
                        "startDateTime": "1985-04-12T23:20:50.52Z"
                    },
                    "@baseType": "string",
                    "@schemaLocation": "string",
                    "@type": "string"
                    }
                ],
                "tolerancePeriod": {
                    "amount": 0,
                    "units": "string"
                },
                "@baseType": "string",
                "@schemaLocation": "string",
                "@type": "string"
                }
            ],
            "validFor": {
                "endDateTime": "1985-04-12T23:20:50.52Z",
                "startDateTime": "1985-04-12T23:20:50.52Z"
            },
            "@baseType": "string",
            "@schemaLocation": "string",
            "@type": "string"
            }
        ],
        "validFor": {
            "endDateTime": "1985-04-12T23:20:50.52Z",
            "startDateTime": "1985-04-12T23:20:50.52Z"
        },
        "@baseType": "string",
        "@schemaLocation": "string",
        "@type": "string"
    }
    return Utils.create_response(success=True, data=response_data)


# SIMULATE THE NODS !!!
@router.get(
    "/Content/{content_id}", 
)
def create_service_test(content_id, db: Session = Depends(get_db)):
    return FileResponse(os.path.join(currentdir, '..', 'test_descriptors_examples', 'base_testing_descriptor.yaml'))


