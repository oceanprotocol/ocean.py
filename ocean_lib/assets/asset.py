#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import copy
import json
import logging
from typing import List, Optional

from enforce_typing import enforce_types

from ocean_lib.agreements.service_types import ServiceTypes
from ocean_lib.assets.credentials import AddressCredential
from ocean_lib.services.service import Service
from ocean_lib.utils.utilities import create_checksum

logger = logging.getLogger("ddo")


@enforce_types
class Asset:
    """Asset class to create, import, export, validate Asset/DDO objects for V4."""

    @enforce_types
    def __init__(
        self,
        did: Optional[str] = None,
        context: Optional[list] = None,
        chain_id: Optional[int] = None,
        nft_address: Optional[str] = None,
        metadata: Optional[dict] = None,
        services: Optional[list] = None,
        credentials: Optional[dict] = None,
        nft: Optional[dict] = None,
        datatokens: Optional[list] = None,
        event: Optional[dict] = None,
        stats: Optional[dict] = None,
    ) -> None:

        self.did = did
        self.context = context or ["https://w3id.org/did/v1"]
        self.chain_id = chain_id
        self.nft_address = nft_address
        self.metadata = metadata
        self.version = "4.0.0"
        self.services = services or []
        self.credentials = credentials or {}
        self.nft = nft
        self.datatokens = datatokens
        self.event = event
        self.stats = stats

    @property
    @enforce_types
    def requires_address_credential(self) -> bool:
        """Checks if an address credential is required on this asset."""
        manager = AddressCredential(self)
        return manager.requires_credential()

    @property
    @enforce_types
    def allowed_addresses(self) -> list:
        """Lists addresses that are explicitly allowed in credentials."""
        manager = AddressCredential(self)
        return manager.get_addresses_of_class("allow")

    @property
    @enforce_types
    def denied_addresses(self) -> list:
        """Lists addresses that are explicitly denied in credentials."""
        manager = AddressCredential(self)
        return manager.get_addresses_of_class("deny")

    @enforce_types
    def add_address_to_allow_list(self, address: str) -> None:
        """Adds an address to allowed addresses list."""
        manager = AddressCredential(self)
        manager.add_address_to_access_class(address, "allow")

    @enforce_types
    def add_address_to_deny_list(self, address: str) -> None:
        """Adds an address to the denied addresses list."""
        manager = AddressCredential(self)
        manager.add_address_to_access_class(address, "deny")

    @enforce_types
    def remove_address_from_allow_list(self, address: str) -> None:
        """Removes address from allow list (if it exists)."""
        manager = AddressCredential(self)
        manager.remove_address_from_access_class(address, "allow")

    @enforce_types
    def remove_address_from_deny_list(self, address: str) -> None:
        """Removes address from deny list (if it exists)."""
        manager = AddressCredential(self)
        manager.remove_address_from_access_class(address, "deny")

    @classmethod
    @enforce_types
    def from_dict(cls, dictionary: dict) -> "Asset":
        """Import a JSON dict into this Asset."""
        values = copy.deepcopy(dictionary)

        services = (
            []
            if "services" not in values
            else [Service.from_dict(value) for value in values.pop("services")]
        )
        return cls(
            values.pop("id"),
            values.pop("@context"),
            values.pop("chainId"),
            values.pop("nftAddress"),
            values.pop("metadata", None),
            services,
            values.pop("credentials", None),
            values.pop("nft", None),
            values.pop("datatokens", None),
            values.pop("event", None),
            values.pop("stats", None),
        )

    @enforce_types
    def as_dictionary(self) -> dict:
        """
        Return the DDO as a JSON dict.

        :return: dict
        """

        data = {
            "@context": self.context,
            "id": self.did,
            "version": self.version,
            "chainId": self.chain_id,
        }

        data["nftAddress"] = self.nft_address

        services = [value.as_dictionary() for value in self.services]
        args = ["metadata", "credentials", "nft", "datatokens", "event", "stats"]
        attrs = list(
            filter(
                lambda attr: not not attr[1],
                map(lambda attr: (attr, getattr(self, attr, None)), args),
            )
        )
        attrs.append(("services", services))
        data.update(attrs)
        return data

    @enforce_types
    def add_service(self, service: Service) -> None:
        """
        Add a service to the list of services on the V4 DDO.

        :param service: To add service, Service
        """

        logger.debug(
            f"Adding service with service type {service.type} with did {self.did}"
        )
        self.services.append(service)

    @enforce_types
    def get_service_by_id(self, service_id: str) -> Service:
        """Return Service with the given id.
        Return None if service with the given id not found."""
        return next(
            (service for service in self.services if service.id == service_id), None
        )

    @enforce_types
    def get_service_by_index(self, service_index: int) -> Service:
        """Return Service with the given index.
        Return None if service with the given index not found."""
        return (
            self.services[service_index] if service_index < len(self.services) else None
        )

    @enforce_types
    def get_service(self, service_type: str) -> Optional[Service]:
        """Return first Service with the given service type.
        Return None if service with the given service type not found."""
        return next(
            (service for service in self.services if service.type == service_type), None
        )

    @enforce_types
    def get_index_of_service(self, service: Service) -> int:
        """Return index of the given Service.
        Return None if service was not found."""
        return next(
            (
                index
                for index, asset_service in enumerate(self.services)
                if asset_service.id == service.id
            ),
            None,
        )

    @enforce_types
    def remove_publisher_trusted_algorithm(
        self, compute_service: Service, algo_did: str
    ) -> list:
        """Returns a trusted algorithms list after removal."""
        trusted_algorithms = compute_service.get_trusted_algorithms()
        if not trusted_algorithms:
            raise ValueError(
                f"Algorithm {algo_did} is not in trusted algorithms of this asset."
            )
        trusted_algorithms = [ta for ta in trusted_algorithms if ta["did"] != algo_did]
        trusted_algo_publishers = compute_service.get_trusted_algorithm_publishers()
        self.update_compute_values(
            trusted_algorithms,
            trusted_algo_publishers,
            allow_network_access=True,
            allow_raw_algorithm=False,
        )
        assert (
            self.get_service("compute").compute_values["publisherTrustedAlgorithms"]
            == trusted_algorithms
        ), "New trusted algorithm was not removed. Failed when updating the list of trusted algorithms. "

        return trusted_algorithms

    @enforce_types
    def remove_publisher_trusted_algorithm_publisher(
        self, compute_service: Service, publisher_address: str
    ) -> list:
        """
        :return: List of trusted algo publishers not containing `publisher_address`.
        """

        trusted_algorithm_publishers = [
            tp.lower() for tp in compute_service.get_trusted_algorithm_publishers()
        ]
        publisher_address = publisher_address.lower()
        if not trusted_algorithm_publishers:
            raise ValueError(
                f"Publisher {publisher_address} is not in trusted algorithm publishers of this asset."
            )

        trusted_algorithm_publishers = [
            tp for tp in trusted_algorithm_publishers if tp != publisher_address
        ]
        trusted_algorithms = compute_service.get_trusted_algorithms()
        self.update_compute_values(
            trusted_algorithms, trusted_algorithm_publishers, True, False
        )
        assert (
            self.get_service("compute").compute_values[
                "publisherTrustedAlgorithmPublishers"
            ]
            == trusted_algorithm_publishers
        ), "New trusted algorithm publisher was not removed. Failed when updating the list of trusted algo publishers. "

        return trusted_algorithm_publishers

    @enforce_types
    def generate_trusted_algorithms(self) -> dict:
        """Returns a trustedAlgorithm dictionary for service at index 0."""
        files = self.get_service_by_index(0).files
        container = self.metadata["algorithm"]["container"]
        return {
            "did": self.did,
            "filesChecksum": create_checksum(files),
            "containerSectionChecksum": create_checksum(
                json.dumps(container, separators=(",", ":"))
            ),
        }

    @enforce_types
    def update_compute_values(
        self,
        trusted_algorithms: List,
        trusted_algo_publishers: Optional[List],
        allow_network_access: bool,
        allow_raw_algorithm: bool,
    ) -> None:
        """Set the `trusted_algorithms` on the compute service.

        - An assertion is raised if this asset has no compute service
        - Updates the compute service in place
        - Adds the trusted algorithms under privacy.publisherTrustedAlgorithms

        :param trusted_algorithms: list of dicts, each dict contain the keys
            ("containerSectionChecksum", "filesChecksum", "did")
        :param trusted_algo_publishers: list of strings, addresses of trusted publishers
        :param allow_network_access: bool -- set to True to allow network access to all the algorithms that belong to this dataset
        :param allow_raw_algorithm: bool -- determine whether raw algorithms (i.e. unpublished) can be run on this dataset
        :return: None
        :raises AssertionError if this asset has no `ServiceTypes.CLOUD_COMPUTE` service
        """
        assert not trusted_algorithms or isinstance(trusted_algorithms, list)
        service = self.get_service(ServiceTypes.CLOUD_COMPUTE)
        assert service is not None, "this asset does not have a compute service."

        for ta in trusted_algorithms:
            assert isinstance(
                ta, dict
            ), f"item in list of trusted_algorithms must be a dict, got {ta}"
            assert (
                "did" in ta
            ), f"dict in list of trusted_algorithms is expected to have a `did` key, got {ta.keys()}."

        if not service.compute_values:
            service.compute_values = {}

        service.compute_values["publisherTrustedAlgorithms"] = trusted_algorithms
        service.compute_values[
            "publisherTrustedAlgorithmPublishers"
        ] = trusted_algo_publishers
        service.compute_values["allowNetworkAccess"] = allow_network_access
        service.compute_values["allowRawAlgorithm"] = allow_raw_algorithm

    @property
    def is_disabled(self) -> bool:
        return not self.metadata or (self.nft and self.nft["state"] != 0)
