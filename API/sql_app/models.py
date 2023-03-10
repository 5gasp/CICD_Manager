# -*- coding: utf-8 -*-
# @Author: Rafael Direito
# @Date:   22-05-2022 10:25:05
# @Email:  rdireito@av.it.pt
# @Last Modified by:   Rafael Direito
# @Last Modified time: 25-05-2022 17:11:06
# @Description: 
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
from email.policy import default
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy import Column, Integer, DateTime, Enum
from sqlalchemy.orm import relationship
import datetime

# custom imports
from .database import Base


class CI_CD_Agent(Base):
	__tablename__ = "ci_cd_nodes"

	id = Column(Integer, primary_key=True, index=True)
	url = Column(String)
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
		# dic.pop("communication_token")
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
	extra_information = Column(String)
	access_token = Column(String, nullable=False)
	test_log_location = Column(String)
	test_results_location = Column(String)
	nods_id = Column(String)

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


class Testing_Artifact(Base):
	__tablename__ = "testing_artifact"

	id = Column(Integer, primary_key=True, index=True)
	test_instance_id = Column(Integer, ForeignKey("test_instances.id"), nullable=False)
	ftp_base_path = Column(String, nullable=False)


	def as_dict(self):
		return {c.name: getattr(self, c.name) for c in self.__table__.columns}



class Test_Instance_Tests(Base):
    __tablename__ = "test_instance_tests"   
    
    id = Column(Integer, primary_key=True, index=True)    
    test_instance = Column(Integer, ForeignKey("test_instances.id"), nullable=False)
    description = Column(String)
    performed_test = Column(String, nullable=False)
    is_developer_defined = Column(Boolean, default=False)
    developer_defined_test_filepath = Column(String, default=None)
    start_time = Column(String)
    end_time = Column(String)
    success = Column(Boolean)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Test_Information(Base):
	__tablename__ = "test_information"
	id  = Column(Integer,primary_key=True, autoincrement=True)
	testid = Column(String)
	name = Column(String)
	testbed_id = Column(String, ForeignKey("testbeds.id"), nullable=False)
	description = Column(String)
	ftp_base_location = Column(String)
	test_filename = Column(String)
	test_type = Column(String)
	testinfo_variables = relationship("Test_Variables",back_populates="test_information")

	def as_dict(self):
		return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Test_Variables(Base):
	__tablename__ = "test_variables"
	id = Column(Integer, primary_key=True, index=True)
	variable_name = Column(String)
	description = Column(String)
	mandatory = Column(Boolean, default=True)
	type = Column(String)
	testinformation_id = Column(Integer, ForeignKey('test_information.id'))
	test_information = relationship("Test_Information",back_populates="testinfo_variables")
	possible_options = relationship("Variable_Options",back_populates='testvariable')
	def as_dict(self):
		return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Variable_Options(Base):
	__tablename__ = "variable_options"
	id = Column(Integer, primary_key=True, index=True)
	name = Column (String)
	testvariable_id = Column(Integer, ForeignKey('test_variables.id'))
	testvariable = relationship("Test_Variables",back_populates='possible_options')
	def as_dict(self):
		return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class User(Base):
	__tablename__ = "user"
	id = Column(Integer, primary_key=True, index=True)    
	username = Column(String, unique=True, index=True)
	hashed_password = Column(String, nullable=False)
	is_active = Column(Boolean, nullable=False)

	def as_dict(self):
		return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class User_Role(Base):
	__tablename__ = "user_role"
	id = Column(Integer, primary_key=True, index=True)    
	user = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
	role = Column(Integer, ForeignKey("role.id"), nullable=False)

	def as_dict(self):
		return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Role(Base):
	__tablename__ = "role"
	id = Column(Integer, primary_key=True, index=True)    
	role = Column(String, unique=True)

	def as_dict(self):
		return {c.name: getattr(self, c.name) for c in self.__table__.columns}

