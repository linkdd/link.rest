# -*- coding: utf-8 -*-


class RestError(Exception):
    pass


class MissingLinkError(RestError):
    pass


class RequestValidationError(RestError):
    pass


class ResponseValidationError(RestError):
    pass
