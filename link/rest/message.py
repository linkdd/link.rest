# -*- coding: utf-8 -*-


class RestMessage(object):
    def __init__(self, status, items=None, links=None, *args, **kwargs):
        super(RestMessage, self).__init__(*args, **kwargs)

        self.status = status
        self.items = items
        self.links = links
