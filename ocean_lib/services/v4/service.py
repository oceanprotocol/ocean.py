#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
"""
    Service Class for V4
    To handle service items in a DDO record
"""
import copy
import logging
from typing import Dict, Any, Optional

from enforce_typing import enforce_types

from ocean_lib.common.agreements.service_types import ServiceTypesV4, ServiceTypesNames

logger = logging.getLogger(__name__)


@enforce_types
class NFTService:
    """Service class to create validate service in a V4 DDO."""

    SERVICE_TYPE = "type"
    SERVICE_FILES = "files"
    SERVICE_NAME = "name"
    SERVICE_DESCRIPTION = "description"
    SERVICE_DATATOKEN = "datatokenAddress"
    SERVICE_ENDPOINT = "serviceEndpoint"
    SERVICE_TIMEOUT = "timeout"

    def __init__(
        self,
        service_type: str,
        service_endpoint: str,
        data_token: str,
        files: str,
        timeout: float,
        other_values: Optional[Dict[str, Any]] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        """Initialize Service instance."""
        self.type = service_type
        self.service_endpoint = service_endpoint
        self.data_token = data_token
        self.files = files
        self.timeout = timeout
        self.name = name
        self.description = description
        self._values = dict()

        self._reserved_names = {
            self.SERVICE_TYPE,
            self.SERVICE_FILES,
            self.SERVICE_NAME,
            self.SERVICE_DESCRIPTION,
            self.SERVICE_DATATOKEN,
            self.SERVICE_ENDPOINT,
            self.SERVICE_TIMEOUT,
        }
        if other_values:
            for key, value in other_values.items():
                if key not in self._reserved_names:
                    self._values[key] = value

        if name is None:
            service_to_default_name = {
                ServiceTypesV4.ASSET_ACCESS: ServiceTypesNames.DEFAULT_ACCESS_NAME,
                ServiceTypesV4.CLOUD_COMPUTE: ServiceTypesNames.DEFAULT_COMPUTE_NAME,
            }

            if service_type in service_to_default_name:
                self.name = service_to_default_name[service_type]

    @classmethod
    @enforce_types
    def from_json(cls, service_dict: Dict[str, Any]) -> "NFTService":
        """Create a service object from a JSON string."""
        sd = copy.deepcopy(service_dict)
        service_type = sd.pop(cls.SERVICE_TYPE, None)
        service_endpoint = sd.pop(cls.SERVICE_ENDPOINT, None)
        data_token = sd.pop(cls.SERVICE_DATATOKEN, None)
        service_files = sd.pop(cls.SERVICE_FILES, None)
        timeout = sd.pop(cls.SERVICE_TIMEOUT, None)
        name = sd.pop(cls.SERVICE_NAME, None)
        description = sd.pop(cls.SERVICE_DESCRIPTION, None)

        if not service_type:
            logger.error(
                'Service definition in DDO document is missing the "type" key/value.'
            )
            raise IndexError

        return cls(
            service_type,
            service_endpoint,
            data_token,
            service_files,
            timeout,
            name,
            description,
        )

    def values(self) -> Dict[str, Any]:
        """

        :return: array of values
        """
        return self._values.copy()

    def as_dictionary(self) -> Dict[str, Any]:
        """Return the service as a python dictionary."""

        values = {
            self.SERVICE_TYPE: self.type,
            self.SERVICE_FILES: self.files,
            self.SERVICE_DATATOKEN: self.data_token,
            self.SERVICE_ENDPOINT: self.service_endpoint,
            self.SERVICE_TIMEOUT: self.timeout,
        }

        if self.name is not None:
            values[self.SERVICE_NAME] = self.name
        if self.description is not None:
            values[self.SERVICE_DESCRIPTION] = self.description

        for key, value in values.items():
            if isinstance(value, object) and hasattr(value, "as_dictionary"):
                value = value.as_dictionary()
            elif isinstance(value, list):
                value = [
                    v.as_dictionary() if hasattr(v, "as_dictionary") else v
                    for v in value
                ]

            values[key] = value

        if self._values:
            values.update(self._values)

        return values
