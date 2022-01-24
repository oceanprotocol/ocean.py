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
from typing import Any, Dict, Optional

from ocean_lib.agreements.consumable import ConsumableCodes
from ocean_lib.agreements.service_types import ServiceTypes, ServiceTypesNames
from ocean_lib.assets.credentials import AddressCredential
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from web3.main import Web3

logger = logging.getLogger(__name__)


class Service:
    """Service class to create validate service in a V4 DDO."""

    def __init__(
        self,
        service_id: str,
        service_type: str,
        service_endpoint: Optional[str],
        datatoken: Optional[str],
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
        self.datatoken = datatoken
        self.files = files
        self.timeout = timeout
        self.compute_values = compute_values
        self.name = name
        self.description = description

        if not name or not description:
            service_to_default_name = {
                ServiceTypes.ASSET_ACCESS: ServiceTypesNames.DEFAULT_ACCESS_NAME,
                ServiceTypes.CLOUD_COMPUTE: ServiceTypesNames.DEFAULT_COMPUTE_NAME,
            }

            if service_type in service_to_default_name:
                self.name = service_to_default_name[service_type]
                self.description = service_to_default_name[service_type]

    @classmethod
    def from_dict(cls, service_dict: Dict[str, Any]) -> "Service":
        """Create a service object from a JSON string."""
        sd = copy.deepcopy(service_dict)
        service_type = sd.pop("type", None)

        if not service_type:
            logger.error(
                'Service definition in DDO document is missing the "type" key/value.'
            )
            raise IndexError

        return cls(
            sd.pop("id", None),
            service_type,
            sd.pop("serviceEndpoint", None),
            sd.pop("datatokenAddress", None),
            sd.pop("files", None),
            sd.pop("timeout", None),
            sd.pop("compute", None),
            sd.pop("name", None),
            sd.pop("description", None),
        )

    @classmethod
    def from_json(cls, service_dict: Dict[str, Any]) -> "Service":
        return cls.from_dict(service_dict)

    def get_trusted_algorithms(self) -> list:
        return self.compute_values.get("publisherTrustedAlgorithms", [])

    def get_trusted_algorithm_publishers(self) -> list:
        return self.compute_values.get("publisherTrustedAlgorithmPublishers", [])

    # Not type provided due to circular imports
    def add_publisher_trusted_algorithm(
        self, algo_ddo, generated_trusted_algo_dict: list
    ) -> list:
        """
        :return: List of trusted algos
        """
        initial_trusted_algos_v4 = self.get_trusted_algorithms()

        # remove algo_did if already in the list
        trusted_algos = [
            ta for ta in initial_trusted_algos_v4 if ta["did"] != algo_ddo.did
        ]
        initial_count = len(trusted_algos)

        trusted_algos.append(generated_trusted_algo_dict)

        # update with the new list
        self.compute_values["publisherTrustedAlgorithms"] = trusted_algos

        assert (
            len(self.compute_values["publisherTrustedAlgorithms"]) > initial_count
        ), "New trusted algorithm was not added. Failed when updating the privacy key. "

        return trusted_algos

    def add_publisher_trusted_algorithm_publisher(self, publisher_address: str) -> list:
        trusted_algo_publishers = [
            Web3.toChecksumAddress(tp) for tp in self.get_trusted_algorithm_publishers()
        ]
        publisher_address = Web3.toChecksumAddress(publisher_address)

        if publisher_address in trusted_algo_publishers:
            return trusted_algo_publishers

        initial_len = len(trusted_algo_publishers)
        trusted_algo_publishers.append(publisher_address)

        # update with the new list
        self.compute_values[
            "publisherTrustedAlgorithmPublishers"
        ] = trusted_algo_publishers
        assert (
            len(self.compute_values["publisherTrustedAlgorithmPublishers"])
            > initial_len
        ), "New trusted algorithm was not added. Failed when updating the privacy key. "

        return trusted_algo_publishers

    def as_dictionary(self) -> Dict[str, Any]:
        """Return the service as a python dictionary."""

        values = {
            "id": self.id,
            "type": self.type,
            "files": self.files,
            "datatokenAddress": self.datatoken,
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

        return values

    def is_consumable(
        self,
        asset,
        credential: Optional[dict] = None,
        with_connectivity_check: bool = True,
    ) -> bool:
        """Checks whether an asset is consumable and returns a ConsumableCode."""
        if asset.is_disabled:
            return ConsumableCodes.ASSET_DISABLED

        if with_connectivity_check and not DataServiceProvider.check_asset_file_info(
            asset.did, self.id, self.service_endpoint
        ):
            return ConsumableCodes.CONNECTIVITY_FAIL

        # to be parameterized in the future, can implement other credential classes
        manager = AddressCredential(asset)

        if manager.requires_credential():
            return manager.validate_access(credential)

        return ConsumableCodes.OK
