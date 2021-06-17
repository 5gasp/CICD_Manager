from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base

class CI_CD_Node(Base):
    __tablename__ = "ci_cd_nodes"

    id = Column(Integer, primary_key=True, index=True)
    ip = Column(String)
    username = Column(String)   
    password = Column(String)
    service_id = Column(String, unique=True, index=True)
    testbed_id = Column(String)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    def as_dict_without_password(self):
       dic = {c.name: getattr(self, c.name) for c in self.__table__.columns}
       dic.pop("password")
       return dic

'''
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

    items = relationship("Item", back_populates="owner")


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="items")
'''