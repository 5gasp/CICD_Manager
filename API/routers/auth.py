from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
# generic imports
from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.sql.functions import user
from API.routers.tests import new_test
from sql_app.database import SessionLocal
from sqlalchemy.orm import Session
import logging
import inspect
import sys
import os
from sql_app import crud
from aux import auth
from aux import constants as Constants
from exceptions.auth import *
import sql_app.schemas.auth as AuthSchemas


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


# to get a string like this run:
# openssl rand -hex 32
#SECRET_KEY = "99cb3e97787cf81a7f418c42b96a06f77ce25ddbb2f7f83a53cf3474896624f9"
#ALGORITHM = "HS256"
#ACCESS_TOKEN_EXPIRE_MINUTES = 60


fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": False,
    }
}



#pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
#oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()


'''
async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@router.get("/users/me/items/")
async def read_own_items(current_user: User = Depends(get_current_active_user)):
    return [{"item_id": "Foo", "owner": current_user.username}]
'''

@router.post("/users/login")
def login_for_access_token(form_data: AuthSchemas.UserLogin, db: Session = Depends(get_db)):
    try:
        user = crud.authenticate_user(db, form_data.username, form_data.password)
        access_token_expires = timedelta(minutes=Constants.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth.create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
    except UserInvalidCredentials as e:
        return Utils.create_response(status_code=401, success=False, errors=[e.message]) 

    return Utils.create_response(status_code=200, success=True, data={"access_token": access_token, "token_type": "Bearer Token"})  


@router.get("/users/me/")
def get_my_information(token: str = Depends(auth.oauth2_scheme), db: Session = Depends(get_db)):
    try:
        username = auth.get_current_user(token)
        user_info = crud.get_user_info(db, username)
    except Exception as e:
        return Utils.create_response(status_code=401, success=False, errors=[e.message]) 

    return Utils.create_response(status_code=200, success=True, data={"user_info": user_info})  


@router.post("/users/register/")
def register_new_user(new_user: AuthSchemas.UserRegister, token: str = Depends(auth.oauth2_scheme), db: Session = Depends(get_db)):
    try:
        login_username = auth.get_current_user(token)
        roles = crud.get_user_roles(db, login_username)
        # check if operation was ordered by an admin
        if "ADMIN" not in roles:
            raise NotEnoughPrivileges(login_username, 'register_new_user')
        # create new user
        db_user = crud.register_user(db, new_user.username, new_user.password, new_user.roles)
        user_info = crud.get_user_info(db, db_user.username)
    except Exception as e:
        return Utils.create_response(status_code=401, success=False, errors=[e.message]) 
    return Utils.create_response(status_code=200, success=True, data={"new_user": user_info})  



@router.patch("/users/update-password/")
def update_password(password_data: AuthSchemas.NewPassword, token: str = Depends(auth.oauth2_scheme) , db: Session = Depends(get_db)):
    try:
        username = auth.get_current_user(token)
        db_user = crud.update_user_password(db, username, password_data.new_password)
    except Exception as e:
        return Utils.create_response(status_code=403, success=False, errors=[e.message]) 
    return Utils.create_response(status_code=200, success=True, message="Password Updated With Success")  

