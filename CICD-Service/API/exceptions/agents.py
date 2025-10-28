from http import HTTPStatus

class AgentAlreadyExists(Exception):
    """Exception raised when an admin wants to create a new CI/CD Agent which already exists .

    Attributes:
        id -- CI/CD Agent's id
        ip -- CI/CD Agent's ip
        username -- CI/CD Agent's username
        testbed_id -- CI/CD Agent's testbed_id
    """

    def __init__(self, id=None, ip=None, username=None, testbed_id=None):
        self.status_code = HTTPStatus.CONFLICT
        if username and id and ip and testbed_id:
            self.username = username
            self.ip = ip
            self.id = id
            self.testbed_id = testbed_id
            self.message = f'The Agent with the IP {self.ip} already exists for the testbed {self.testbed_id}. Agent\'s id: {self.id}'
        else:
           self.message = 'These agent already exists' 
        super().__init__(self.message)

    def __str__(self):
        return self.message


class AgentDoesNotExist(Exception):
    """Exception raised when a CI/CD Agent doesn't exist .

    Attributes:
        id -- CI/CD Agent's id
    """

    def __init__(self, id=None):
        self.status_code = HTTPStatus.NOT_MODIFIED
        if id:
            self.id = id
            self.message = f'The Agent with the Id {self.id} doesn\'t exist'
        else:
           self.message = 'These agent doesn\'t exist' 
        super().__init__(self.message)

    def __str__(self):
        return self.message
