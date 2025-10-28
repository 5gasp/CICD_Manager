from pydantic import BaseModel, Field
from typing import Any, List

class TestVariables(BaseModel):
    variable_name: str = Field(...,example= "host1_ip")
    description: str = Field(...,example= "Login username for Host/VNF 1")
    mandatory: bool = True
    type: str = Field(...,example="str")
    possible_options: List[Any]

class TestInformation(BaseModel):
    testid: str = Field(...,example= "bandwidth")
    name : str = Field(...,example= "bandwidth")
    testbed_id: str = Field(...,example= "testbed_xyz")
    description: str = Field(...,example= "Tests the bandwidth between to VNFs. The results are in bits/sec")
    ftp_base_location: str = Field(...,example= "tests/bandwidth/")
    test_filename: str = Field(...,example= "testBandwidth.robot")
    test_type: str = Field(...,example= "Robot")
    test_variables: List[TestVariables]


class TestInformationUpdate(TestInformation):
    name : str = None
    testbed_id: str = None
    description: str = None
    ftp_base_location: str = None
    test_filename: str = None
    test_type: str = None
    test_variables: List[TestVariables] = []

class TestBaseInformation(BaseModel):
    test_id: str  
    netapp_id: str
    network_service_id: str
    testbed_id: str
    started_at: str
    test_status: str

class TestResults(BaseModel):
    id: int    
    test_instance: int
    description: str
    performed_test: str
    start_time: str
    end_time: str
    success = bool