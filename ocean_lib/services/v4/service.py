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

from ocean_lib.common.agreements.service_types import ServiceTypesV4, ServiceTypesNames

logger = logging.getLogger(__name__)


class NFTService:
    """Service class to create validate service in a V4 DDO."""

    SERVICE_TYPE = "type"
    SERVICE_ID = "serviceId"
    SERVICE_FILES = "files"
    SERVICE_NAME = "name"
    SERVICE_DESCRIPTION = "description"
    SERVICE_DATATOKEN = "datatokenAddress"
    SERVICE_ENDPOINT = "serviceEndpoint"
    SERVICE_TIMEOUT = "timeout"
    SERVICE_COMPUTE = "compute"

    def __init__(
        self,
        service_id: str,
        service_type: str,
        service_endpoint: Optional[str],
        data_token: Optional[str],
        files: Optional[str],
        timeout: Optional[int],
        compute_values: Optional[Dict[str, Any]] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        """Initialize NFT Service instance."""
        self.id = service_id
        self.type = service_type
        self.service_endpoint = service_endpoint
        self.data_token = data_token
        self.files = files
        self.timeout = timeout
        self.compute_values = compute_values
        self.name = name
        self.description = description
        self._values = dict()

        if name is None:
            service_to_default_name = {
                ServiceTypesV4.ASSET_ACCESS: ServiceTypesNames.DEFAULT_ACCESS_NAME,
                ServiceTypesV4.CLOUD_COMPUTE: ServiceTypesNames.DEFAULT_COMPUTE_NAME,
            }

            if service_type in service_to_default_name:
                self.name = service_to_default_name[service_type]

    @classmethod
    def from_json(cls, service_dict: Dict[str, Any]) -> "NFTService":
        """Create a service object from a JSON string."""
        sd = copy.deepcopy(service_dict)
        service_id = sd.pop(cls.SERVICE_ID, None)
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
            service_id,
            service_type,
            service_endpoint,
            data_token,
            service_files,
            timeout,
            sd,
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
            self.SERVICE_ID: self.id,
            self.SERVICE_TYPE: self.type,
            self.SERVICE_FILES: self.files,
            self.SERVICE_DATATOKEN: self.data_token,
            self.SERVICE_ENDPOINT: self.service_endpoint,
            self.SERVICE_TIMEOUT: self.timeout,
        }

        if self.SERVICE_COMPUTE in self.compute_values:
            if (
                self.compute_values is not None
                and len(self.compute_values.values()) > 0
            ):
                values.update(self.compute_values)
        else:
            if (
                self.compute_values is not None
                and len(self.compute_values.values()) > 0
            ):
                values[self.SERVICE_COMPUTE] = self.compute_values

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
