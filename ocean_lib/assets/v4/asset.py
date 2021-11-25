# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import copy
import json
import logging

from typing import Optional, List

from enforce_typing import enforce_types

from ocean_lib.assets.credentials import AddressCredential
from ocean_lib.common.agreements.service_types import ServiceTypesV4
from ocean_lib.services.v4.service import V4Service

logger = logging.getLogger("ddo")


@enforce_types
class V4Asset:
    """Asset class to create, import, export, validate Asset/DDO objects for V4."""

    def __init__(
        self,
        did: Optional[str] = None,
        context: Optional[list] = None,
        chain_id: Optional[int] = None,
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
        self.metadata = metadata
        self.version = "4.0.0"
        self.services = services or []
        self.credentials = credentials or {}
        self.nft = nft
        self.datatokens = datatokens
        self.event = event
        self.stats = stats

    @property
    def requires_address_credential(self) -> bool:
        """Checks if an address credential is required on this asset."""
        manager = AddressCredential(self)
        return manager.requires_credential()

    @property
    def allowed_addresses(self) -> list:
        """Lists addresses that are explicitly allowed in credentials."""
        manager = AddressCredential(self)
        return manager.get_addresses_of_class("allow")

    @property
    def denied_addresses(self) -> list:
        """Lists addresses that are explicitly denied in credentials."""
        manager = AddressCredential(self)
        return manager.get_addresses_of_class("deny")

    def add_address_to_allow_list(self, address: str) -> None:
        """Adds an address to allowed addresses list."""
        manager = AddressCredential(self)
        manager.add_address_to_access_class(address, "allow")

    def add_address_to_deny_list(self, address: str) -> None:
        """Adds an address to the denied addresses list."""
        manager = AddressCredential(self)
        manager.add_address_to_access_class(address, "deny")

    def remove_address_from_allow_list(self, address: str) -> None:
        """Removes address from allow list (if it exists)."""
        manager = AddressCredential(self)
        manager.remove_address_from_access_class(address, "allow")

    def remove_address_from_deny_list(self, address: str) -> None:
        """Removes address from deny list (if it exists)."""
        manager = AddressCredential(self)
        manager.remove_address_from_access_class(address, "deny")

    @classmethod
    def from_dict(cls, dictionary: dict) -> "V4Asset":
        """Import a JSON dict into this Asset."""
        values = copy.deepcopy(dictionary)
        id_key = "id" if "id" in values else "_id"
        services = []
        if "services" in values:
            for value in values.pop("services"):
                if isinstance(value, str):
                    value = json.loads(value)

                service = V4Service.from_json(value)
                services.append(service)
        return cls(
            values.pop(id_key),
            values.pop("@context"),
            values.pop("chainId"),
            values.pop("metadata", None),
            services,
            values.pop("credentials", None),
            values.pop("nft", None),
            values.pop("datatokens", None),
            values.pop("event", None),
            values.pop("stats", None),
        )

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

        services = [
            self.services.append(service.as_dictionary())
            for service in self.services
            if isinstance(service, V4Service)
        ]
        self.services = list(filter(lambda s: isinstance(s, dict), services))

        args = [
            "metadata",
            "services",
            "credentials",
            "nft",
            "datatokens",
            "event",
            "stats",
        ]
        attrs = list(
            filter(
                lambda attr: not not attr[1],
                map(lambda attr: (attr, getattr(self, attr, None)), args),
            )
        )
        data.update(attrs)
        return data

    def add_service(self, service: V4Service) -> None:
        """
        Add a service to the list of services on the V4 DDO.

        :param service: To add service, V4Service
        """

        logger.debug(
            f"Adding service with service type {service.type} with did {self.did}"
        )
        self.services.append(service)

    def get_service_by_id(self, service_id: str) -> V4Service:
        """Return the Service with the matching id"""
        return next((service for service in self.services if service.id == service_id))

    def get_service(self, service_type: str) -> Optional[V4Service]:
        """Return the first Service with the given service type."""
        return next(
            (service for service in self.services if service.type == service_type),
            None,
        )

    def remove_publisher_trusted_algorithm(
        self, compute_service: V4Service, algo_did: str
    ) -> list:
        """Returns a trusted algorithms list after removal."""
        trusted_algorithms = compute_service.get_trusted_algorithms()
        if not trusted_algorithms:
            raise ValueError(
                f"Algorithm {algo_did} is not in trusted algorithms of this asset."
            )
        trusted_algorithms = [ta for ta in trusted_algorithms if ta["did"] != algo_did]
        trusted_algo_publishers = compute_service.get_trusted_algorithm_publishers()
        self.update_compute_values_v4(
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

    def remove_publisher_trusted_algorithm_publisher(
        self,
        compute_service: V4Service,
        publisher_address: str,
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
        service = self.get_service(ServiceTypesV4.CLOUD_COMPUTE)
        assert service is not None, "this asset does not have a compute service."

        trusted_algorithms = trusted_algorithms if trusted_algorithms else []
        if trusted_algorithms:
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
