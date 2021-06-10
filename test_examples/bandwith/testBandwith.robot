*** Settings ***
Library        Bandwith.py

*** Test Cases ***
Testing the transmission speed between OBU and vOBU

    ${MB_sec}=    Bandwith
    Should Be Equal    ${MB_sec}    The bandwith is bigger than 0.1 MB/sec
