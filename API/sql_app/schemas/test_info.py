from pydantic import BaseModel, Field
from typing import Any, List

class TestVariables(BaseModel):
    variable_name: str
    description: str
    mandatory: bool = True
    type: str = "str" 
    possible_options: List[Any]

class TestInformation(BaseModel):
    id: str
    name : str
    testbed_id: str
    description: str
    ftp_base_location: str
    test_filename: str
    test_type: str
    test_variables: List[TestVariables]