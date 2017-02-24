class UnauthorizedException(Exception):
    def __init__(self, code=401, response={}):

        self.code = code
        # We envelope error messages like this
        self.message = response.get("message", "Unknown Error")
        super(UnauthorizedException, self).__init__()

    def __str__(self):
        return "\n Code: {} \n Message: {} \n".format(self.code, self.message)


class NotFoundException(Exception):
    def __init__(self, code=404, response={}):

        self.code = code
        # We envelope error messages like this
        self.message = response.get("message", "Unknown Error")
        super(NotFoundException, self).__init__()

    def __str__(self):
        return "\n Code: {} \n Message: {} \n".format(self.code, self.message)


class BadRequestException(Exception):
    def __init__(self, code=400, response={}):

        self.code = code
        # We envelope error messages like this
        self.message = response.get("message", "Unknown Error")
        super(BadRequestException, self).__init__()

    def __str__(self):
        return "\n Code: {} \n Message: {} \n".format(self.code, self.message)
