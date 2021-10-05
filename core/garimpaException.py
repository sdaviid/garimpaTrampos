
class Error(Exception):
    pass


class NotExpectedStatusCode(Error):
    pass


class AccessTokenNotFound(Error):
    pass
