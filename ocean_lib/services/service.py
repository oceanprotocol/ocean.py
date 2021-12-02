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
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from enforce_typing import enforce_types
from ocean_lib.agreements.service_types import ServiceTypes, ServiceTypesIndices
from ocean_lib.data_provider.data_service_provider import DataServiceProvider

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

        if index is None:
            service_to_default_index = {
                ServiceTypes.ASSET_ACCESS: ServiceTypesIndices.DEFAULT_ACCESS_INDEX,
                ServiceTypes.CLOUD_COMPUTE: ServiceTypesIndices.DEFAULT_COMPUTING_INDEX,
            }

            if service_type in service_to_default_index:
                self.index = service_to_default_index[service_type]

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
    def from_json(cls, service_dict: Dict[str, Any]) -> "Service":
        """Create a service object from a JSON string."""
        sd = copy.deepcopy(service_dict)
        service_endpoint = sd.pop(cls.SERVICE_ENDPOINT, None)
        service_type = sd.pop(cls.SERVICE_TYPE, None)
        index = sd.pop(cls.SERVICE_INDEX, None)
        attributes = sd.pop(cls.SERVICE_ATTRIBUTES, None)

        if not service_type:
            logger.error(
                'Service definition in DDO document is missing the "type" key/value.'
            )
            raise IndexError

        return cls(service_endpoint, service_type, attributes, sd, index)

    @enforce_types
    def get_cost(self) -> float:
        """
        Return the price from the conditions parameters.

        :return: Float
        """
        return float(self.main["cost"])

    @enforce_types
    def get_c2d_address(self) -> str:
        result = urlparse(self.service_endpoint)
        return DataServiceProvider.get_c2d_address(
            f"{result.scheme}://{result.netloc}/"
        )

    @enforce_types
    def get_trusted_algorithms(self) -> list:
        return (
            self.attributes["main"]
            .get("privacy", {})
            .get("publisherTrustedAlgorithms", [])
        )

    @enforce_types
    def get_trusted_algorithm_publishers(self) -> list:
        return (
            self.attributes["main"]
            .get("privacy", {})
            .get("publisherTrustedAlgorithmPublishers", [])
        )

    # Not type provided due to circular imports
    def add_publisher_trusted_algorithm(
        self,
        algo_ddo,
        generated_trusted_algo_dict: list,
    ) -> list:
        """
        :return: List of trusted algos
        """

        privacy_values = self.attributes["main"].get("privacy")
        if not privacy_values:
            privacy_values = {}
            self.attributes["main"]["privacy"] = privacy_values

        assert isinstance(privacy_values, dict), "Privacy key is not a dictionary."
        trusted_algos = privacy_values.get("publisherTrustedAlgorithms", [])
        # remove algo_did if already in the list
        trusted_algos = [ta for ta in trusted_algos if ta["did"] != algo_ddo.did]

        # now add this algo_did as trusted algo
        trusted_algos.append(generated_trusted_algo_dict)

        # update with the new list
        privacy_values["publisherTrustedAlgorithms"] = trusted_algos
        assert (
            self.attributes["main"]["privacy"] == privacy_values
        ), "New trusted algorithm was not added. Failed when updating the privacy key. "
        return trusted_algos

    @enforce_types
    def add_publisher_trusted_algorithm_publisher(self, publisher_address: str) -> list:
        """
        :return: List of trusted algo publishers
        """

        privacy_values = self.attributes["main"].get("privacy")
        if not privacy_values:
            privacy_values = {}
            self.attributes["main"]["privacy"] = privacy_values

        assert isinstance(privacy_values, dict), "Privacy key is not a dictionary."
        trusted_algo_publishers = [
            tp.lower()
            for tp in privacy_values.get("publisherTrustedAlgorithmPublishers", [])
        ]
        publisher_address = publisher_address.lower()

        if publisher_address in trusted_algo_publishers:
            return trusted_algo_publishers

        trusted_algo_publishers.append(publisher_address)

        # update with the new list
        privacy_values["publisherTrustedAlgorithmPublishers"] = trusted_algo_publishers
        assert (
            self.attributes["main"]["privacy"] == privacy_values
        ), "New trusted algorithm was not added. Failed when updating the privacy key. "
        return trusted_algo_publishers
