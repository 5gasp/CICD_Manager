from http import HTTPStatus


class UserInvalidCredentials(Exception):
    """Exception raised for errors in the credential validation for a user.

    Attributes:
        username -- username for which the credentials are invalid
    """

    def __init__(self, username=None):
        if username:
            self.username = username
            self.message = f'Invalid credentials for User {self.username}'
        else:
           self.message = 'Invalid credentials' 
        super().__init__(self.message)

    def __str__(self):
        return self.message


class UserNotActive(Exception):
    """Exception raised when a user which is not active is trying to make an operation.

    Attributes:
        username -- username regarding the user who is not active
    """

    def __init__(self, username=None):
        if username:
            self.username = username
            self.message = f'User {self.username} is not active'
        else:
           self.message = 'User is not active'
        super().__init__(self.message)

    def __str__(self):
        return self.message


class UserDoesNorExist(Exception):
    """Exception raised when a user doesn't exist.

    Attributes:
        username -- username regarding the user who is not active
    """

    def __init__(self, username=None):
        if username:
            self.username = username
            self.message = f'User {self.username} doesn\'t exist'
        else:
           self.message = 'User doesn\'t exist'
        super().__init__(self.message)

    def __str__(self):
        return self.message


class UserAlreadyExists(Exception):
    """Exception raised when a user already exists.

    Attributes:
        username -- username regarding the user who is not active
    """

    def __init__(self, username=None):
        if username:
            self.username = username
            self.message = f'User {self.username} already exists'
        else:
           self.message = 'User already exists'
        super().__init__(self.message)

    def __str__(self):
        return self.message


class UserCreationFailed(Exception):
    """Exception raised when an error occurs when creating a user.

    Attributes:
        username -- username regarding the user who is not active
    """

    def __init__(self, username=None):
        if username:
            self.username = username
            self.message = f'Error in creating the user with the username {self.username}'
        else:
           self.message = 'Error in creating the user'
        super().__init__(self.message)

    def __str__(self):
        return self.message


class CouldNotDecodeBearerToken(Exception):
    """Exception raised when it is impossible to decode the bearer token.
    """
    
    def __init__(self):
        self.status_code = HTTPStatus.FORBIDDEN
        self.message = 'Could not decode Bearer Token'
        super().__init__(self.message)

    def __str__(self):
        return self.message


class InvalidUser(Exception):
    """Exception raised when a user is invalid.

    Attributes:
        username -- username regarding the user who is not active
    """

    def __init__(self, username=None):
        if username:
            self.username = username
            self.message = f'Invalid user {self.username}'
        else:
           self.message = 'Invalid user'
        super().__init__(self.message)

    def __str__(self):
        return self.message


class NotEnoughPrivileges(Exception):
    """Exception raised when a user is trying to perform an operation without the needed privileges.

    Attributes:
        username -- username regarding the user who is not active
        operation -- intended operation
    """
    def __init__(self, username=None, operation=None):
        if username:
            self.username = username
            self.operation = operation
            self.message = f'Not enough privileges for user {self.username} to perform the operation {self.operation}'
        else:
           self.message = 'Not enough privileges'
        super().__init__(self.message)

    def __str__(self):
        return self.message


class PasswordUpdateFailed(Exception):
    """Exception raised when an error occurs when updating a user's password.

    Attributes:
        username -- username regarding the user who is not active
    """

    def __init__(self, username=None):
        if username:
            self.username = username
            self.message = f'Could not update {username}\'s passsword'
        else:
           self.message = 'Error in updating user\'s password'
        super().__init__(self.message)

    def __str__(self):
        return self.message
