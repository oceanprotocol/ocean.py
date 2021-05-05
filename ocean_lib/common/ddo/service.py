#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
"""
    Service Class
    To handle service items in a DDO record
"""
import copy
import logging

logger = logging.getLogger(__name__)


class Service:
    """Service class to create validate service in a DDO."""

    SERVICE_ENDPOINT = "serviceEndpoint"
    SERVICE_TYPE = "type"
    SERVICE_INDEX = "index"
    SERVICE_ATTRIBUTES = "attributes"

    def __init__(
        self, service_endpoint, service_type, attributes, other_values=None, index=None
    ):
        """Initialize Service instance."""
        self._service_endpoint = service_endpoint
        self._type = service_type or ""
        self._index = index
        self._attributes = attributes or {}

        # assign the _values property to empty until they are used
        self._values = dict()
        self._reserved_names = {
            self.SERVICE_ENDPOINT,
            self.SERVICE_TYPE,
            self.SERVICE_INDEX,
        }
        if other_values:
            for name, value in other_values.items():
                if name not in self._reserved_names:
                    self._values[name] = value

    @property
    def type(self):
        """
        Type of the service.

        :return: str
        """
        return self._type

    @property
    def index(self):
        """
        Identifier of the service inside the asset DDO

        :return: str
        """
        return self._index

    @property
    def service_endpoint(self):
        """
        Service endpoint.

        :return: String
        """
        return self._service_endpoint

    def set_service_endpoint(self, service_endpoint):
        """
        Update service endpoint. Needed to update after create did.

        :param service_endpoint: Service endpoint, str
        """
        self._service_endpoint = service_endpoint

    def values(self):
        """

        :return: array of values
        """
        return self._values.copy()

    @property
    def attributes(self):
        return self._attributes

    @property
    def main(self):
        return self._attributes["main"]

    def update_value(self, name, value):
        """
        Update value in the array of values.

        :param name: Key of the value, str
        :param value: New value, str
        :return: None
        """
        if name not in self._reserved_names:
            self._values[name] = value

    def as_dictionary(self):
        """Return the service as a python dictionary."""
        attributes = {}
        for key, value in self._attributes.items():
            if isinstance(value, object) and hasattr(value, "as_dictionary"):
                value = value.as_dictionary()
            elif isinstance(value, list):
                value = [
                    v.as_dictionary() if hasattr(v, "as_dictionary") else v
                    for v in value
                ]

            attributes[key] = value

        values = {self.SERVICE_TYPE: self._type, self.SERVICE_ATTRIBUTES: attributes}
        if self._service_endpoint:
            values[self.SERVICE_ENDPOINT] = self._service_endpoint
        if self._index is not None:
            values[self.SERVICE_INDEX] = self._index

        if self._values:
            values.update(self._values)

        return values

    @classmethod
    def _parse_json(cls, service_dict):
        sd = copy.deepcopy(service_dict)
        service_endpoint = sd.pop(cls.SERVICE_ENDPOINT, None)
        _type = sd.pop(cls.SERVICE_TYPE, None)
        _index = sd.pop(cls.SERVICE_INDEX, None)
        _attributes = sd.pop(cls.SERVICE_ATTRIBUTES, None)

        if not _type:
            logger.error(
                'Service definition in DDO document is missing the "type" key/value.'
            )
            raise IndexError

        return service_endpoint, _type, _index, _attributes, sd

    @classmethod
    def from_json(cls, service_dict):
        """Create a service object from a JSON string."""
        service_endpoint, _type, _index, _attributes, sd = cls._parse_json(service_dict)
        return cls(service_endpoint, _type, _attributes, sd, _index)
