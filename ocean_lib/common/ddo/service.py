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
from typing import Any, Dict, Optional, Tuple

from enforce_typing import enforce_types

logger = logging.getLogger(__name__)


class Service:
    """Service class to create validate service in a DDO."""

    SERVICE_ENDPOINT = "serviceEndpoint"
    SERVICE_TYPE = "type"
    SERVICE_INDEX = "index"
    SERVICE_ATTRIBUTES = "attributes"

    def __init__(
        self,
        service_endpoint: Optional[str],
        service_type: str,
        attributes: Optional[Dict],
        other_values: Optional[Dict[str, Any]] = None,
        index: Optional[int] = None,
    ) -> None:
        """Initialize Service instance."""
        # init can not be type hinted due to conflicts with ServiceAgreement
        self.service_endpoint = service_endpoint
        self.type = service_type or ""
        self.index = index
        self.attributes = attributes or {}

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

    @enforce_types
    def values(self) -> Dict[str, Any]:
        """

        :return: array of values
        """
        return self._values.copy()

    @property
    @enforce_types
    def main(self) -> Dict[str, Any]:
        return self.attributes["main"]

    @enforce_types
    def update_value(self, name: str, value: Any) -> None:
        """
        Update value in the array of values.

        :param name: Key of the value, str
        :param value: New value, str
        :return: None
        """
        if name not in self._reserved_names:
            self._values[name] = value

    @enforce_types
    def as_dictionary(self) -> Dict[str, Any]:
        """Return the service as a python dictionary."""
        attributes = {}
        for key, value in self.attributes.items():
            if isinstance(value, object) and hasattr(value, "as_dictionary"):
                value = value.as_dictionary()
            elif isinstance(value, list):
                value = [
                    v.as_dictionary() if hasattr(v, "as_dictionary") else v
                    for v in value
                ]

            attributes[key] = value

        values = {self.SERVICE_TYPE: self.type, self.SERVICE_ATTRIBUTES: attributes}
        if self.service_endpoint:
            values[self.SERVICE_ENDPOINT] = self.service_endpoint
        if self.index is not None:
            values[self.SERVICE_INDEX] = self.index

        if self._values:
            values.update(self._values)

        return values

    @classmethod
    @enforce_types
    def _parse_json(
        cls, service_dict: Dict[str, Any]
    ) -> Tuple[str, str, int, Dict, Dict]:
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
    @enforce_types
    def from_json(cls, service_dict: Dict[str, Any]) -> "Service":
        """Create a service object from a JSON string."""
        service_endpoint, _type, _index, _attributes, sd = cls._parse_json(service_dict)
        return cls(service_endpoint, _type, _attributes, sd, _index)
