



# CI/CD Manager

This python module contains the API of the 5GASP CI/CD Manager. 

## What will you need to use this API

* **An FTP server** - to store the tests that will be performed
* **A Jenkins instance** - to act as the Test Execution Engine (TEE)

For now, you may use an independent Jenkins Instance, but, later, a VNF with Jenkins will be deployed alongside with all the VNFs of the NetApp. Jenkins will then dynamically connect to the CI/CD Manager, that will send it some test jobs.

## FTP Server Files

In `tee_api/test_examples` you can find 2 robot tests. Upload theses tests to your FTP Server.
 
## CI/CD Manager - Base Configuration

Before running the API you will have to define the following environment variables:
* FTP_USER
* FTP_PASSWORD
* FTP_URL
* JENKINS_USER
* JENKINS_PASSWORD
* JENKINS_URL 

## CI/CD Manager - Run the API

To run the API:
```python
cd tee_api
uvicorn main:app --reload
```

## CI/CD Manager - Create a new testing job

Using Postman, you can send the following request:
![Postman Example](https://i.imgur.com/TJfVf4I.png)

In `tee_api/test_descriptors_examples/`  you can find some example testing descriptors.
