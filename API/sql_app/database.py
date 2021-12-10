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
import time
import logging
# load config
config = configparser.ConfigParser()
config.read('config.ini')

# Logger
logging.basicConfig(
    format="%(module)-15s:%(levelname)-10s| %(message)s",
    level=logging.INFO
)

# Test config
try:
    # Load Variables
    Constants.DB_LOCATION = config['DB']['Location']
    Constants.DB_NAME = config['DB']['Name']
    Constants.DB_USER = config['DB']['User']
    Constants.DB_PASSWORD = config['DB']['Password']
except:
    exit(2)

DB_OK = False
for i in range(10):
    try:
        logging.info(f"Trying to connect to the DB - postgresql://{Constants.DB_USER}:{Constants.DB_PASSWORD}@{Constants.DB_LOCATION}/{Constants.DB_NAME}")
        SQLALCHEMY_DATABASE_URL = f"postgresql://{Constants.DB_USER}:{Constants.DB_PASSWORD}@{Constants.DB_LOCATION}/{Constants.DB_NAME}"
        engine = create_engine(
            SQLALCHEMY_DATABASE_URL
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base = declarative_base()
        DB_OK = True
        break
    except:
        logging.error("Waiting for DB. Will sleep 10 more seconds...")
        time.sleep(10)

if not DB_OK:
    logging.critical("Unable to connect to database. Exception:", e)
    exit(2)