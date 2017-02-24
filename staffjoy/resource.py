import time
from datetime import datetime
from copy import copy
import requests

from staffjoy.config import config_from_env
from staffjoy.exceptions import UnauthorizedException, NotFoundException, BadRequestException

MICROSECONDS_PER_SECOND = 10**6

class Resource:
    # Slow each request to this (bc of rate limits)
    REQUEST_TIME_MICROSECONDS = 0.3 * MICROSECONDS_PER_SECOND # 0.3 seconds

    PATH = ""  # URL path added to base, including route variables
    ID_NAME = None  # What is this ID called in the route of children?
    META_ENVELOPES = []  # Metadata keys for what to unpack from response
    ENVELOPE = "data"  # We "envelope" response data in the "data" section
    TRUTHY_CODES = [requests.codes.ok, requests.codes.created,
                    requests.codes.no_content, requests.codes.accepted]

    def __init__(self,
                 key="",
                 config=None,
                 env="prod",
                 data={},
                 route={},
                 meta={}):
        """Initialize the resource"""
        self.key = key

        self.config = config or config_from_env.get(env, "prod")

        # These should be overridden by child classes
        self.data = data  # Data from the read method
        self.route = route  # Route variables
        self.meta = meta  # Meta data

    @classmethod
    def get(cls, parent=None, id=None, data=None):
        """Inherit info from parent and return new object"""
        # TODO - allow fetching of parent based on child?

        if parent is not None:
            route = copy(parent.route)
        else:
            route = {}

        if id is not None and cls.ID_NAME is not None:
            route[cls.ID_NAME] = id

        obj = cls(key=parent.key, route=route, config=parent.config)

        if data:
            # This is used in "get all" queries
            obj.data = data
        else:
            obj.fetch()

        return obj

    @classmethod
    def get_all(cls, parent=None, **params):

        if parent is not None:
            route = copy(parent.route)
        else:
            route = {}
        if cls.ID_NAME is not None:
            # Empty string triggers "get all resources"
            route[cls.ID_NAME] = ""

        base_obj = cls(key=parent.key, route=route, config=parent.config)
        """Perform a read request against the resource"""

        start = datetime.now()
        r = requests.get(base_obj._url(),
                         auth=(base_obj.key, ""),
                         params=params)
        cls._delay_for_ratelimits(start)

        if r.status_code not in cls.TRUTHY_CODES:
            return base_obj._handle_request_exception(r)

        response = r.json()
        objects_data = response.get(base_obj.ENVELOPE or base_obj, [])

        return_objects = []
        for data in objects_data:
            # Note that this approach does not get meta data
            return_objects.append(cls.get(parent=parent,
                                          id=data.get(cls.ID_NAME, data.get(
                                              "id")),
                                          data=data))

        return return_objects

    def _url(self):
        """Get the URL for the resource"""
        if self.ID_NAME not in self.route.keys() and "id" in self.data.keys():
            self.route[self.ID_NAME] = self.data["id"]
        return self.config.BASE + self.PATH.format(**self.route)

    @staticmethod
    def _handle_request_exception(request):
        """Raise the proper exception based on the response"""
        try:
            data = request.json()
        except:
            data = {}

        code = request.status_code
        if code == requests.codes.bad:
            raise BadRequestException(response=data)

        if code == requests.codes.unauthorized:
            raise UnauthorizedException(response=data)

        if code == requests.codes.not_found:
            raise NotFoundException(response=data)

        # Generic error fallback
        request.raise_for_status()

    def fetch(self):
        """Perform a read request against the resource"""
        start = datetime.now()
        r = requests.get(self._url(), auth=(self.key, ""))
        self._delay_for_ratelimits(start)

        if r.status_code not in self.TRUTHY_CODES:
            return self._handle_request_exception(r)

        response = r.json()
        if self.ENVELOPE:
            self.data = response.get(self.ENVELOPE, {})
        else:
            self.data = response

        # Move to separate function so it can be overrridden
        self._process_meta(response)

    def _process_meta(self, response):
        """Process additional data sent in response"""
        for key in self.META_ENVELOPES:
            self.meta[key] = response.get(key)

    def delete(self):
        """Delete the object"""

        start = datetime.now()
        r = requests.delete(self._url(), auth=(self.key, ""))
        self._delay_for_ratelimits(start)

        if r.status_code not in self.TRUTHY_CODES:
            return self._handle_request_exception(r)

    def patch(self, **kwargs):
        """Change attributes of the item"""
        start = datetime.now()
        r = requests.patch(self._url(), auth=(self.key, ""), data=kwargs)
        self._delay_for_ratelimits(start)

        if r.status_code not in self.TRUTHY_CODES:
            return self._handle_request_exception(r)

        # Refetch for safety. We could modify based on response,
        # but I'm afraid of some edge cases and marshal functions.
        self.fetch()

    @classmethod
    def create(cls, parent=None, **kwargs):
        """Create an object and return it"""

        if parent is None:
            raise Exception("Parent class is required")

        route = copy(parent.route)
        if cls.ID_NAME is not None:
            route[cls.ID_NAME] = ""

        obj = cls(key=parent.key, route=route, config=parent.config)

        start = datetime.now()
        response = requests.post(obj._url(), auth=(obj.key, ""), data=kwargs)
        cls._delay_for_ratelimits(start)

        if response.status_code not in cls.TRUTHY_CODES:
            return cls._handle_request_exception(response)

        # No envelope on post requests
        data = response.json()
        obj.route[obj.ID_NAME] = data.get("id", data.get(obj.ID_NAME))
        obj.data = data

        return obj

    def get_id(self):
        return self.data.get("id", self.route.get(self.ID_NAME))

    @classmethod
    def _delay_for_ratelimits(cls, start):
        """If request was shorter than max request time, delay"""
        stop = datetime.now()
        duration_microseconds = (stop-start).microseconds
        if duration_microseconds < cls.REQUEST_TIME_MICROSECONDS:
            time.sleep((cls.REQUEST_TIME_MICROSECONDS - duration_microseconds) / MICROSECONDS_PER_SECOND)

    def __str__(self):
        return "{} id {}".format(self.__class__.__name__,
                                 self.route.get(self.ID_NAME))
