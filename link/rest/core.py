# -*- coding: utf-8 -*-

from b3j0f.conf import Configurable, category
from b3j0f.utils.path import lookup

from link.rest.exceptions import MultipleLinksMatchingError
from link.rest.exceptions import ResponseValidationError
from link.rest.exceptions import RequestValidationError
from link.rest.exceptions import MissingLinkError
from link.rest import CONF_BASE_PATH

from link.json.exceptions import JsonValidationError
from link.json.schema import JsonSchema
from link.wsgi.url import parse_qs

from six import raise_from
from parse import parse


@Configurable(
    paths='{0}/api.conf'.format(CONF_BASE_PATH),
    conf=category('RESTAPI')
)
class SchemaApi(object):
    def __init__(self, schema, *args, **kwargs):
        super(SchemaApi, self).__init__(*args, **kwargs)

        self.validator = JsonSchema()
        self.schema = schema

    def get_links(self, method, url):
        links = []

        for link in self.schema['links']:
            urldata = parse(link['href'], url)
            smethod = self.schema.get('method', 'GET')

            if urldata is not None and method == smethod:
                links.append({
                    'link': link,
                    'data': urldata
                })

        return links

    def validate_request(self, method, url, content, query):
        matches = self.get_links(method, url)

        if not matches:
            raise MissingLinkError(
                'No link matching: {0} {1}'.format(method, url)
            )

        elif len(matches) > 1:
            raise MultipleLinksMatchingError(
                'There is {0} matches for: {0} {1}'.format(
                    len(matches),
                    method,
                    url
                )
            )

        link = matches[0]

        body = link['data']
        body.update(parse_qs(content))
        body.update(query)

        try:
            self.validator.validate(link['link'].get('schema', {}), body)

        except JsonValidationError as err:
            raise_from(
                RequestValidationError(str(err)),
                err
            )

        return body

    def execute(self, method, url, request):
        link = self.get_links(method, url)[0]
        handler = lookup(link['link']['rel'])

        return handler(**request)

    def validate_response(self, method, url, response):
        link = self.get_links(method, url)[0]

        try:
            self.validator.validate(
                link['link'].get('targetSchema', {}),
                response
            )

        except JsonValidationError as err:
            raise_from(
                ResponseValidationError(str(err)),
                err
            )
