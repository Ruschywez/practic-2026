class UserNotFoundError(Exception):
    pass
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