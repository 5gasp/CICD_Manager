#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Author: Rafael Direito (rdireito@av.it.pt)
# Date:  7th june 2021
# Last Update: 12th july 2021

# Description:
# Contains the definition of the information that will be stored in the database. 
# Mapping of python classes to database objects, using ORM


# generic imports
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy import Column, Integer, DateTime
import datetime

# custom imports
from .database import Base


class CI_CD_Node(Base):
    __tablename__ = "ci_cd_nodes"

    id = Column(Integer, primary_key=True, index=True)
    netapp_id = Column(String, nullable=False)
    network_service_id = Column(String,nullable=False)
    ip = Column(String)
    username = Column(String)
    password = Column(String)
    testbed_id = Column(String, ForeignKey("testbeds.id"), nullable=False)
    communication_token = Column(String)
    is_online = Column(Boolean)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def as_dict_without_password(self):
        dic = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        dic.pop("password")
        dic.pop("communication_token")
        return dic


class Testbed(Base):
    __tablename__ = "testbeds"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True)
    description = Column(String)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Test_Instance(Base):
    __tablename__ = "test_instances"

    id = Column(Integer, primary_key=True, index=True)
    netapp_id = Column(String, nullable=False)
    network_service_id = Column(String, nullable=False)
    build = Column(Integer)
    testbed_id = Column(String, ForeignKey("testbeds.id"), nullable=False)
    ci_cd_node_id = Column(Integer, ForeignKey("ci_cd_nodes.id"), nullable=True)
  

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Test_Status(Base):
    __tablename__ = "test_status"

    id = Column(Integer, primary_key=True, index=True)
    timestamp =  Column(DateTime, default=datetime.datetime.utcnow)
    test_id = Column(Integer, ForeignKey("test_instances.id"), nullable=False)
    state = Column(String, nullable=False)
    success = Column(Boolean, nullable=False)


    def as_dict(self):
        dic =  {c.name: getattr(self, c.name) for c in self.__table__.columns}
        dic["timestamp"] = self.timestamp.isoformat()
        return dic