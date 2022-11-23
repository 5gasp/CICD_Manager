#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Author: Rafael Direito (rdireito@av.it.pt)
# Date: 8th November 2021
# Last Update: 8th November 2021

# Description:
# TMF653 Integration - Schemas

from codecs import namereplace_errors
from datetime import datetime
from os import name
# generic imports
from typing import Any, List

from pydantic import BaseModel, Field
from sql_app.database import Base


class Quantity(BaseModel):
    amount: float = None
    units: str = None


class TimePeriod(BaseModel):
    endDateTime: datetime = None
    startDateTime: datetime = None

class ConstraintRef(BaseModel):
    id: str = None
    href: str = None
    name: str = None
    version: str = None
    baseType: str = Field(default=None, alias='@baseType')
    schemaLocation:str = Field(default=None, alias='@schemaLocation')
    type:str = Field(default=None, alias='@type')

    
class AttachmentRefOrValue(BaseModel):
    id: str = None
    href: str = None
    attachmentType: str = None
    content: str = None
    description: str = None
    mimeType: str = None
    name: str = None
    url: str = None
    size: Quantity = None
    validFor: TimePeriod = None
    baseType: str = Field(default=None, alias='@baseType')
    schemaLocation:str = Field(default=None, alias='@schemaLocation')
    type:str = Field(default=None, alias='@type')
    referredType: str = Field(alias='@referredType')

class CharacteristicRelationship(BaseModel):
    id: str = None
    href: str = None
    relationshipType: str = None
    baseType: str = Field(default=None, alias='@baseType')
    schemaLocation:str = Field(default=None, alias='@schemaLocation')
    type:str = Field(default=None, alias='@type')


# class Any(BaseModel):
#     # No implementation provided by the TMF653 Standard
#     pass


class AppliedConsequence(BaseModel):
    appliedAction: str = None
    description: str = None
    name: str = None
    repeatAction: bool = None
    baseType: str = Field(default=None, alias='@baseType')
    schemaLocation:str = Field(default=None, alias='@schemaLocation')
    type:str = Field(default=None, alias='@type')


class Duration(BaseModel):
    amount: int = None
    units: str = None


class MeasureThresholdRuleViolation(BaseModel):
    conformanceComparatorExact: bool = None
    conformanceComparatorLower: str = None
    conformanceComparatorUpper: str = None
    conformanceTargetExact: str = None
    conformanceTargetLower: str = None
    conformanceTargetUpper: str = None	
    description: str = None
    name: str = None
    numberOfAllowedCrossing: int = None
    thresholdRuleSeverity: str = None
    appliedConsequence: List[AppliedConsequence] = None
    tolerancePeriod: Duration = None
    baseType: str = Field(default=None, alias='@baseType')
    schemaLocation:str = Field(default=None, alias='@schemaLocation')
    type:str = Field(default=None, alias='@type')


class Characteristic(BaseModel):
    id: str = None
    name: str
    valueType: str = None
    characteristicRelationship: List[CharacteristicRelationship] = None
    value: Any = None # @Todo Should be Any 
    baseType: str = Field(default=None, alias='@baseType')
    schemaLocation:str = Field(default=None, alias='@schemaLocation')
    type:str = Field(default=None, alias='@type')


class RelatedParty(BaseModel):
    id: str
    href: str = None
    name: str = None
    role: str = None
    baseType: str = Field(default=None, alias='@baseType')
    schemaLocation:str = Field(default=None, alias='@schemaLocation')
    type:str = Field(default=None, alias='@type')
    referredType: str = Field(alias='@referredType')


class ServiceRef(BaseModel):
    id: str
    href: str = None
    name: str = None
    baseType: str = Field(default=None, alias='@baseType')
    schemaLocation:str = Field(default=None, alias='@schemaLocation')
    type:str = Field(default=None, alias='@type')
    referredType: str = Field(default=None, alias='@referredType')


class TestMeasure(BaseModel):
    accuracy: float = None
    captureDateTime: datetime = None
    captureMethod: str = None
    metricDescription: str = None
    metricHref: str = None
    metricName: str = None
    unitOfMeasure: str = None
    ruleViolation: List[MeasureThresholdRuleViolation] = None
    value: Characteristic = None
    baseType: str = Field(default=None, alias='@baseType')
    schemaLocation:str = Field(default=None, alias='@schemaLocation')
    type:str = Field(default=None, alias='@type')


class ServiceTestSpecificationRef(BaseModel):
    id: str
    href: str = None
    version: str = None
    baseType: str = Field(default=None, alias='@baseType')
    schemaLocation:str = Field(default=None, alias='@schemaLocation')
    type:str = Field(default=None, alias='@type')
    referredType: str = Field(default=None, alias='@referredType')



class ServiceTest_Create(BaseModel):
    description: str = None
    endDateTime: datetime = None
    mode: str = None
    name: str
    startDateTime: datetime = None
    state: str = None
    characteristic: List[Characteristic] = None
    relatedParty: List[RelatedParty] = None
    relatedService: ServiceRef
    testMeasure: List[TestMeasure] = None
    testSpecification: ServiceTestSpecificationRef
    validFor: TimePeriod = None
    baseType: str = Field(default=None, alias='@baseType')
    schemaLocation:str = Field(default=None, alias='@schemaLocation')
    type:str = Field(default=None, alias='@type')

    class Config:
        orm_mode = True


class AssociationSpecificationRef(BaseModel):
    id: str
    href: str = None
    name: str = None
    baseType: str = Field(default=None, alias='@baseType')
    schemaLocation:str = Field(default=None, alias='@schemaLocation')
    type:str = Field(default=None, alias='@type')
    referredType: str = Field(default=None, alias='@referredType')


class EntitySpecificationRelationship(BaseModel):
    id: str = None
    href: str = None
    name: str = None
    relationshipType: str
    role: str = None
    associationSpec: AssociationSpecificationRef = None
    validFor: TimePeriod = None
    baseType: str = Field(default=None, alias='@baseType')
    schemaLocation:str = Field(default=None, alias='@schemaLocation')
    type:str = Field(default=None, alias='@type')

class ServiceSpecificationRef(BaseModel):
    id: str
    href: str = None
    name: str = None
    version: str = None
    baseType: str = Field(default=None, alias='@baseType')
    schemaLocation:str = Field(default=None, alias='@schemaLocation')
    type:str = Field(default=None, alias='@type')
    referredType: str = Field(default=None, alias='@referredType')


class ServiceTestSpecRelationship(BaseModel):
    id: str = None
    href: str = None
    name: str = None
    relationshipType: str
    role: str = None
    validFor: TimePeriod = None
    baseType: str = Field(default=None, alias='@baseType')
    schemaLocation:str = Field(default=None, alias='@schemaLocation')
    type:str = Field(default=None, alias='@type')
    referredType: str = Field(default=None, alias='@referredType')


class CharacteristicSpecificationRelationship(BaseModel):
    characteristicSpecificationId: str = None
    name: str = None
    parentSpecificationHref: str = None
    parentSpecificationId: str = None
    relationshipType: str = None
    validFor: TimePeriod = None
    baseType: str = Field(default=None, alias='@baseType')
    schemaLocation:str = Field(default=None, alias='@schemaLocation')
    type:str = Field(default=None, alias='@type')


class CharacteristicValueSpecification(BaseModel):
    isDefault: bool = None
    rangeInterval: str = None
    regex: str = None
    unitOfMeasure: str = None
    valueFrom: int = None
    valueTo: int = None
    valueType: str = None
    validFor: TimePeriod = None
    value: str = None # @Todo Should be Any 
    baseType: str = Field(default=None, alias='@baseType')
    schemaLocation:str = Field(default=None, alias='@schemaLocation')
    type:str = Field(default=None, alias='@type')


class CharacteristicSpecification(BaseModel):
    id: str = None
    configurable: bool = None
    description: str = None
    extensible: bool = None
    isUnique: bool = None
    maxCardinality: int = None
    minCardinality: int = None
    name: str = None
    regex: str = None
    valueType: str = None
    charSpecRelationship: List[CharacteristicSpecificationRelationship] = None
    characteristicValueSpecification: List[CharacteristicValueSpecification] = None
    validFor: TimePeriod = None
    baseType: str = Field(default=None, alias='@baseType')
    schemaLocation:str = Field(default=None, alias='@schemaLocation')
    type:str = Field(default=None, alias='@type')
    valueSchemaLocation: str = Field(default=None, alias='@valueSchemaLocation')


class TargetEntitySchema(BaseModel):
    schemaLocation:str = Field(default=None, alias='@schemaLocation')
    type:str = Field(default=None, alias='@type')


class MetricDefMeasureConsequence(BaseModel):
    description: str = None
    name: str = None
    prescribeAction: str = None
    repeatAction: bool = None
    validFor: TimePeriod = None
    baseType: str = Field(default=None, alias='@baseType')
    schemaLocation:str = Field(default=None, alias='@schemaLocation')
    type:str = Field(default=None, alias='@type')


class MetricDefMeasureThresholdRule(BaseModel):
    conformanceComparatorExact: str = None
    conformanceComparatorLower: str = None
    conformanceComparatorUpper: str = None
    conformanceTargetExact: str = None
    conformanceTargetLower: str = None
    conformanceTargetUpper: str = None
    description: str = None
    name: str = None
    numberOfAllowedCrossing: int = None
    thresholdRuleSeverity: str = None
    consequence: List[MetricDefMeasureConsequence] = None
    tolerancePeriod: Duration = None
    baseType: str = Field(default=None, alias='@baseType')
    schemaLocation:str = Field(default=None, alias='@schemaLocation')
    type:str = Field(default=None, alias='@type')


class TestMeasureDefinition(BaseModel):
    captureFrequency: str = None
    captureMethod: str = None
    metricDescription: str = None
    metricHref: str = None
    metricName: str = None
    name: str = None
    unitOfMeasure: str = None
    valueType: str = None
    capturePeriod: Duration = None
    thresholdRule: List[MetricDefMeasureThresholdRule] = None
    validFor: TimePeriod = None
    baseType: str = Field(default=None, alias='@baseType')
    schemaLocation:str = Field(default=None, alias='@schemaLocation')
    type:str = Field(default=None, alias='@type')


class ServiceTestSpecification(BaseModel):
    id: str = None
    href: str = None
    description: str = None
    isBundle: bool = None
    lastUpdate: datetime = None
    lifecycleStatus: str = None
    name: str = None
    version: str = None
    attachment: List[AttachmentRefOrValue] = None
    constraint: List[ConstraintRef] = None
    entitySpecRelationship: List[EntitySpecificationRelationship] = None
    relatedParty: List[RelatedParty] = None
    relatedServiceSpecification: List[ServiceSpecificationRef] = None
    serviceTestSpecRelationship: List[ServiceTestSpecRelationship] = None
    specCharacteristic: List[CharacteristicSpecification] = None
    targetEntitySchema: TargetEntitySchema = None
    testMeasureDefinition: List[TestMeasureDefinition] = None
    validFor: TimePeriod = None
    baseType: str = Field(default=None, alias='@baseType')
    schemaLocation:str = Field(default=None, alias='@schemaLocation')
    type:str = Field(default=None, alias='@type')

    class Config:
        orm_mode = True