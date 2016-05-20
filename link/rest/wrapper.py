# -*- coding: utf-8 -*-

from six.moves.urllib.parse import urlunsplit, urlencode, SplitResult
from six import string_types

from b3j0f.conf import Configurable, category, Parameter
from b3j0f.utils.runtime import singleton_per_scope

from link.rest.exceptions import MissingLinkError
from link.rest.exceptions import MultipleLinksMatchingError
from link.rest.exceptions import RequestValidationError
from link.rest.exceptions import ResponseValidationError
from link.rest.message import RestMessage
from link.rest.core import SchemaApi
from link.rest import CONF_BASE_PATH

from link.json.collection import generate_collection_response
from link.json.resolver import JsonResolver


@Configurable(
    paths='{0}/wrapper.conf'.format(CONF_BASE_PATH),
    conf=category(
        'RESTWRAPPER',
        Parameter('schemas')
    )
)
class RestWrapper(object):

    DEFAULT_SCHEMAS = {}

    @property
    def schemas(self):
        if not hasattr(self, '_schemas'):
            self.schemas = None

        return self._schemas

    @schemas.setter
    def schemas(self, value):
        if value is None:
            value = RestWrapper.DEFAULT_SCHEMAS

        if isinstance(value, string_types):
            value = self.resolver(value)

        for key in value:
            if isinstance(value[key], string_types):
                value[key] = self.resolver(value[key])

        self._schemas = value

    def __init__(self, *args, **kwargs):
        super(RestWrapper, self).__init__(*args, **kwargs)

        self.resolver = JsonResolver()

    def get_collection_href(self, req, href=None):
        selfurl = urlunsplit(
            SplitResult(
                scheme=req.protocol,
                host=req.server_host,
                port=req.server_port
            )
        )

        if href is not None:
            href = '{0}/{1}'.format(selfurl, href)

        else:
            href = selfurl

        return href

    def __call__(self, req, resp):
        path = filter(lambda p: p, req.path.split('/'))

        if not path:
            if req.method == 'GET':
                resp.status = 200
                resp.content = generate_collection_response(
                    self.get_collection_href(req),
                    links=[
                        {
                            "rel": schemaname,
                            "href": self.get_collection_href(req, schemaname)
                        }
                        for schemaname in self.schemas
                    ]
                )

            else:
                resp.status = 405
                resp.content = generate_collection_response(
                    self.get_collection_href(req),
                    links=[
                        {
                            "rel": "self",
                            "href": self.get_collection_href(req),
                            "method": "GET"
                        }
                    ],
                    error={
                        'title': 'Invalid method',
                        'code': '405 Method not allowed',
                        'message': '{0} method not allowed'.format(req.method)
                    }
                )

        else:
            schema = self.schemas[path[0]]
            api = SchemaApi(schema)

            requrl = '/{0}?{1}'.format(
                '/'.join(path[1:]),
                urlencode(req.query)
            )

            try:
                reqbody = api.validate_request(
                    req.method,
                    requrl,
                    req.content,
                    req.query
                )

                result = api.execute(req.method, requrl, reqbody)

                api.validate_response(req.method, requrl, result)

                if isinstance(result, tuple):
                    msg = RestMessage(
                        result[0],
                        items=result[1],
                        links=result[2]
                    )

                elif isinstance(result, dict):
                    msg = RestMessage(
                        result['status'],
                        items=result.get('items', None),
                        links=result.get('links', None)
                    )

                elif isinstance(result, int):
                    msg = RestMessage(result['status'])

                else:
                    msg = result

                resp.status = msg.status
                resp.content = generate_collection_response(
                    self.get_collection_href(req, '/'.join(path)),
                    items=msg.items,
                    links=msg.links,
                    schema=schema
                )

            except MissingLinkError as err:
                resp.status = 404
                resp.content = generate_collection_response(
                    self.get_collection_href(req, '/'.join(path)),
                    schema=schema,
                    error={
                        'title': 'Missing link error',
                        'code': '404 Not Found',
                        'message': str(err)
                    }
                )

            except MultipleLinksMatchingError as err:
                resp.status = 300
                resp.content = generate_collection_response(
                    self.get_collection_href(req, '/'.join(path)),
                    schema=schema,
                    error={
                        'title': 'Multiple links matching error',
                        'code': '300 Multiple Choices',
                        'message': str(err)
                    }
                )

            except RequestValidationError as err:
                resp.status = 400
                resp.content = generate_collection_response(
                    self.get_collection_href(req, '/'.join(path)),
                    schema=schema,
                    error={
                        'title': 'Request validation error',
                        'code': '400 Bad Request',
                        'message': str(err)
                    }
                )

            except ResponseValidationError as err:
                resp.status = 500
                resp.content = generate_collection_response(
                    self.get_collection_href(req, '/'.join(path)),
                    schema=schema,
                    error={
                        'title': 'Response validation error',
                        'code': '500 Internal Server Error',
                        'message': str(err)
                    }
                )

            except NotImplementedError as err:
                resp.status = 501
                resp.content = generate_collection_response(
                    self.get_collection_href(req, '/'.join(path)),
                    schema=schema,
                    error={
                        'title': 'Not implemented error',
                        'code': '501 Not Implemented',
                        'message': str(err)
                    }
                )

            except Exception as err:
                resp.status = 500
                resp.content = generate_collection_response(
                    self.get_collection_href(req, '/'.join(path)),
                    schema=schema,
                    error={
                        'title': 'Unhandled exception',
                        'code': '500 Internal Server Error',
                        'message': str(err)
                    }
                )


def rest_api_wrapper(req, resp):
    wrapper = singleton_per_scope(RestWrapper)
    return wrapper(req, resp)
