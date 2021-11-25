#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Author: Rafael Direito (rdireito@av.it.pt)
# Date:  7th june 2021
# Last Update: 12th july 2021

# Description:
# Contains the connection to the CI/CD Manager's Database

import aux.constants as Constants
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import configparser

# load config
config = configparser.ConfigParser()
config.read('config.ini')

# Test config
try:
    # Load Variables
    Constants.DB_LOCATION = config['DB']['Location']
    Constants.DB_NAME = config['DB']['Name']
    Constants.DB_USER = config['DB']['User']
    Constants.DB_PASSWORD = config['DB']['Password']
except:
    exit(2)

SQLALCHEMY_DATABASE_URL = f"postgresql://{Constants.DB_USER}:{Constants.DB_PASSWORD}@{Constants.DB_LOCATION}/{Constants.DB_NAME}"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()