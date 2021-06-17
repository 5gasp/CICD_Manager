from pydantic import BaseModel
from typing import Optional

class CI_CD_Node(BaseModel):
    netapp_id: str
    username: str
    password: str
    ip: str
    testbed: str