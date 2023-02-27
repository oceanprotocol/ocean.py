#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import copy
import logging
from typing import Optional

from enforce_typing import enforce_types

from ocean_lib.assets.credentials import AddressCredentialMixin
from ocean_lib.data_provider.fileinfo_provider import FileInfoProvider
from ocean_lib.ocean.util import create_checksum
from ocean_lib.services.service import Service

logger = logging.getLogger("ddo")


class DDO(AddressCredentialMixin):
    """Create, import, export, validate DDO objects."""

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
        self.version = "4.1.0"
        self.services = services or []
        self.credentials = credentials or {}
        self.nft = nft
        self.datatokens = datatokens
        self.event = event
        self.stats = stats

    @property
    @enforce_types
    def requires_address_credential(self) -> bool:
        """Checks if an address credential is required on this ddo."""
        return self.requires_credential()

    @property
    @enforce_types
    def allowed_addresses(self) -> list:
        """Lists addresses that are explicitly allowed in credentials."""
        return self.get_addresses_of_class("allow")

    @property
    @enforce_types
    def denied_addresses(self) -> list:
        """Lists addresses that are explicitly denied in credentials."""
        return self.get_addresses_of_class("deny")

    @enforce_types
    def add_address_to_allow_list(self, address: str) -> None:
        """Adds an address to allowed addresses list."""
        self.add_address_to_access_class(address, "allow")

    @enforce_types
    def add_address_to_deny_list(self, address: str) -> None:
        """Adds an address to the denied addresses list."""
        self.add_address_to_access_class(address, "deny")

    @enforce_types
    def remove_address_from_allow_list(self, address: str) -> None:
        """Removes address from allow list (if it exists)."""
        self.remove_address_from_access_class(address, "allow")

    @enforce_types
    def remove_address_from_deny_list(self, address: str) -> None:
        """Removes address from deny list (if it exists)."""
        self.remove_address_from_access_class(address, "deny")

    @classmethod
    @enforce_types
    def from_dict(cls, dictionary: dict) -> "DDO":
        """Import a JSON dict into this DDO."""
        values = copy.deepcopy(dictionary)

        services = (
            []
            if "services" not in values
            else [Service.from_dict(value) for value in values.pop("services")]
        )

        args = [
            values.pop("id", None),
            values.pop("@context", None),
            values.pop("chainId", None),
            values.pop("nftAddress", None),
            values.pop("metadata", None),
            services,
            values.pop("credentials", None),
            values.pop("nft", None),
            values.pop("datatokens", None),
            values.pop("event", None),
            values.pop("stats", None),
        ]

        if args[0] is None:
            return UnavailableDDO(*args)

        return cls(*args)

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
        service.encrypt_files(self.nft_address, self.chain_id)

        logger.debug(
            f"Adding service with service type {service.type} with did {self.did}"
        )
        self.services.append(service)

    @enforce_types
    def create_compute_service(
        self,
        service_id: str,
        service_endpoint: str,
        datatoken_address: str,
        files,
        compute_values: Optional[dict] = None,
        timeout: Optional[int] = 3600,
    ) -> None:
        if not compute_values:
            compute_values = {
                "allowRawAlgorithm": False,
                "allowNetworkAccess": True,
                "publisherTrustedAlgorithms": [],
                "publisherTrustedAlgorithmPublishers": [],
            }

        compute_service = Service(
            service_id=service_id,
            service_type="compute",
            service_endpoint=service_endpoint,
            datatoken=datatoken_address,
            files=files,
            timeout=timeout,
            compute_values=compute_values,
        )

        self.add_service(compute_service)

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
    def get_index_of_service(self, service: Service) -> int:
        """Return index of the given Service.
        Return None if service was not found."""
        return next(
            (
                index
                for index, this_service in enumerate(self.services)
                if this_service.id == service.id
            ),
            None,
        )

    @enforce_types
    def generate_trusted_algorithms(self) -> dict:
        """Returns a trustedAlgorithm dictionary for service at index 0."""
        resp = FileInfoProvider.fileinfo(
            self.did, self.get_service_by_index(0), with_checksum=True
        )
        files_checksum = [resp_item["checksum"] for resp_item in resp.json()]
        container = self.metadata["algorithm"]["container"]
        return {
            "did": self.did,
            "filesChecksum": "".join(files_checksum),
            "containerSectionChecksum": create_checksum(
                container["entrypoint"] + container["checksum"]
            ),
        }

    @property
    def is_disabled(self) -> bool:
        return not self.metadata or (self.nft and self.nft["state"] not in [0, 5])


class UnavailableDDO(DDO):
    pass
