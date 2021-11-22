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


class V4Service:
    """Service class to create validate service in a V4 DDO."""

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
    def from_dict(cls, service_dict: Dict[str, Any]) -> "V4Service":
        """Create a service object from a JSON string."""
        sd = copy.deepcopy(service_dict)
        service_id = sd.pop("serviceId", None)
        service_type = sd.pop("type", None)
        service_endpoint = sd.pop("serviceEndpoint", None)
        data_token = sd.pop("datatokenAddress", None)
        service_files = sd.pop("files", None)
        timeout = sd.pop("timeout", None)
        name = sd.pop("name", None)
        description = sd.pop("description", None)
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

    @classmethod
    def from_json(cls, service_dict: Dict[str, Any]) -> "V4Service":
        return cls.from_dict(service_dict)

    def values(self) -> Dict[str, Any]:
        """

        :return: array of values
        """
        return dict()

    def add_trusted_algo_publisher_v4(self, new_publisher_address: str) -> list:
        trusted_algo_publishers = [
            tp.lower()
            for tp in self.compute_values.get("publisherTrustedAlgorithmPublishers", [])
        ]
        publisher_address = new_publisher_address.lower()

        if publisher_address in trusted_algo_publishers:
            return trusted_algo_publishers

        trusted_algo_publishers.append(publisher_address)
        initial_len = len(trusted_algo_publishers)
        # update with the new list
        self.compute_values[
            "publisherTrustedAlgorithmPublishers"
        ] = trusted_algo_publishers
        assert (
            len(self.compute_values["publisherTrustedAlgorithmPublishers"])
            > initial_len
        ), "New trusted algorithm was not added. Failed when updating the privacy key. "
        return trusted_algo_publishers

    def get_trusted_algos_v4(self) -> list:
        trusted_algos = self.compute_values.get("publisherTrustedAlgorithms", [])
        return trusted_algos

    def as_dictionary(self) -> Dict[str, Any]:
        """Return the service as a python dictionary."""

        values = {
            "serviceId": self.id,
            "type": self.type,
            "files": self.files,
            "datatokenAddress": self.data_token,
            "serviceEndpoint": self.service_endpoint,
            "timeout": self.timeout,
        }

        if self.type == "compute":
            if "compute" in self.compute_values:
                values.update(self.compute_values)
            else:
                values["compute"] = self.compute_values

        if self.name is not None:
            values["name"] = self.name
        if self.description is not None:
            values["description"] = self.description

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
