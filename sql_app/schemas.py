from typing import List, Optional

from pydantic import BaseModel


# --------------- CI/CD Nodes --------------- #

class CI_CD_Node_Base(BaseModel):
    ip: str
    username: str
    service_id: str
    testbed_id: str

class CI_CD_Node_Create(CI_CD_Node_Base):
    password: str

class CI_CD_Node(CI_CD_Node_Base):
    id: int

    class Config:
        orm_mode = True

# --------------- end of CI/CD Nodes --------------- #

'''
class ItemBase(BaseModel):
    title: str
    description: Optional[str] = None


class ItemCreate(ItemBase):
    pass


class Item(ItemBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool
    items: List[Item] = []

    class Config:
        orm_mode = True
'''