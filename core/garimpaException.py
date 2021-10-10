
class Error(Exception):
    pass


class t(Error):
    pass


class NotExpectedStatusCode(Error):
    pass


class AccessTokenNotFound(Error):
    pass



class WrongLengthCEP(Error):
    pass



class FailedGetVacancyData(Error):
    pass