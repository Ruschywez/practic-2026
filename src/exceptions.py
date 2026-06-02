class WrongPasswordError(Exception):
    pass
class AvatarNotFoundError(Exception):
    pass
class ConflictError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)
class SecretNotFoundError(Exception):
    pass
class SecretImageNotFoundError(Exception):
    pass
class ValidationError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)
class NotFoundError(Exception):
    def __init__(self, message=""):
        super().__init__(message)
class InvalidSession(Exception):
    pass
class AlreadyExistsError(Exception):
    pass
class SessionError(Exception):
    def __init__(self, message=""):
        super().__init__(message)