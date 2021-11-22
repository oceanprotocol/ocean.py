# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import copy
import json
import logging
import os

from typing import Optional

from enforce_typing import enforce_types

from ocean_lib.assets.credentials import AddressCredential
from ocean_lib.common.agreements.service_types import ServiceTypesV4
from ocean_lib.ocean.util import get_web3
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
        self.metadata = metadata
        self.version = "4.0.0"
        self.services = services or []
        self.credentials = credentials or {}
        self.nft = nft
        self.datatokens = datatokens
        self.event = event
        self.stats = stats

        network_url = os.getenv("OCEAN_NETWORK_URL")
        if chain_id:
            self.chain_id = chain_id
        elif network_url:
            w3 = get_web3(network_url)
            self.chain_id = w3.eth.chain_id
        else:
            raise TypeError(f"The chain ID is not provided.")

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
        did = values.pop(id_key)
        chain_id = values.pop("chainId")
        context = values.pop("@context")

        if "metadata" in values:
            metadata = values.pop("metadata")
        if "services" in values:
            services = []
            for value in values.pop("services"):
                if isinstance(value, str):
                    value = json.loads(value)

                service = V4Service.from_json(value)
                services.append(service)
        if "credentials" in values:
            credentials = values.pop("credentials")
        if "nft" in values:
            nft = values.pop("nft")
        if "datatokens" in values:
            data_tokens = values.pop("datatokens")
        if "event" in values:
            event = values.pop("event")
        if "stats" in values:
            stats = values.pop("stats")
        return cls(
            did,
            context,
            chain_id,
            metadata,
            services,
            credentials,
            nft,
            data_tokens,
            event,
            stats,
        )

    def as_dictionary(self) -> dict:
        """
        Return the DDO as a JSON dict.

        :return: dict
        """

        data = {
            "@context": ["https://w3id.org/did/v1"],
            "id": self.did,
            "version": self.version,
            "chainId": self.chain_id,
        }

        for value in self.services:
            if isinstance(value, V4Service):
                service = value.as_dictionary()
                self.services.append(service)

        self.services = list(filter(lambda s: isinstance(s, dict), self.services))

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
