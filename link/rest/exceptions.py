# -*- coding: utf-8 -*-


class RestError(Exception):
    pass


class MultipleLinksMatchingError(RestError):
    pass


class MissingLinkError(RestError):
    pass


class RequestValidationError(RestError):
    pass


class ResponseValidationError(RestError):
    pass
