# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import copy
import json
import logging
import os
from pathlib import Path
from typing import Optional, List, Union

from enforce_typing import enforce_types
from eth_utils import add_0x_prefix

from ocean_lib.assets.credentials import AddressCredential
from ocean_lib.assets.did import did_to_id
from ocean_lib.ocean.util import get_web3
from ocean_lib.services.v4.service import NFTService

logger = logging.getLogger("ddo")


@enforce_types
class V4Asset:
    """Asset class to create, import, export, validate Asset/DDO objects for V4."""

    def __init__(
        self,
        asset_dict: Optional[dict] = None,
        json_text: Optional[str] = None,
        json_filename: Optional[Path] = None,
    ) -> None:

        self.version = "4.0.0"
        self._services = []
        self.credentials = {}

        network_url = os.getenv("OCEAN_NETWORK_URL")
        if network_url:
            w3 = get_web3(network_url)
            self._chain_id = w3.eth.chain_id
        else:
            raise TypeError(f"The network URL is not provided.")

        if not json_text and json_filename:
            with open(json_filename, "r") as file_handle:
                json_text = file_handle.read()
        if json_text:
            self._read_dict(json.loads(json_text))
        elif asset_dict:
            self._read_dict(asset_dict)

    @property
    def asset_id(self) -> Optional[str]:
        """The asset id part of the DID"""
        if not self.did:
            return None
        return add_0x_prefix(did_to_id(self.did))

    @property
    def metadata(self) -> Optional[dict]:
        """Get the metadata."""
        return self._metadata

    @property
    def chain_id(self) -> int:
        """Get the chain ID."""
        return self._chain_id

    @property
    def services(self) -> List[dict]:
        """Get the chain ID."""
        return self._services

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
        """Lists addresesses that are explicitly denied in credentials."""
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

    def _read_dict(self, dictionary: dict) -> None:
        """Import a JSON dict into this Asset."""
        values = copy.deepcopy(dictionary)
        id_key = "id" if "id" in values else "_id"
        self.did = values.pop(id_key)
        self._chain_id = values.pop("chainId")

        if "metadata" in values:
            self._metadata = values.pop("metadata")
        if "services" in values:
            self._services = []
            for value in values.pop("services"):
                if isinstance(value, str):
                    value = json.loads(value)

                service = NFTService.from_json(value)
                self._services.append(service)
        if "credentials" in values:
            self.credentials = values.pop("credentials")
        if "nft" in values:
            self.nft = values.pop("nft")
        if "datatokens" in values:
            self.data_tokens = values.pop("datatokens")
        if "event" in values:
            self.event = values.pop("event")
        if "stats" in values:
            self.stats = values.pop("stats")

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

        if self._metadata:
            data["metadata"] = self._metadata
        if self.services:
            data["services"] = [service.as_dictionary() for service in self._services]
        if self.credentials:
            data["credentials"] = self.credentials
        if self.nft:
            data["nft"] = self.nft
        if self.data_tokens:
            data["datatokens"] = self.data_tokens
        if self.event:
            data["event"] = self.event
        if self.stats:
            data["stats"] = self.stats

        return data

    def as_text(self, is_pretty: bool = False) -> str:
        """Return the V4 DDO as a JSON text.

        :param is_pretty: If True return dictionary in a prettier way, bool
        :return: str
        """
        data = self.as_dictionary()
        if is_pretty:
            return json.dumps(data, indent=2, separators=(",", ": "))

        return json.dumps(data)

    def add_service(
        self,
        service_id: str,
        service_type: Union[str, NFTService],
        service_endpoint: Optional[str] = None,
        data_token: Optional[str] = None,
        files: Optional[str] = None,
        timeout: Optional[int] = None,
        compute_values: Optional[dict] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        """
        Add a service to the list of services on the V4 DDO.

        :param service_id: Unique identifier of the service, str
        :param service_type: Service
        :param service_endpoint: Service endpoint, str
        :param data_token: Data token address, str
        :param files: Encrypted files URLS, str
        :param timeout: Duration of the service in seconds, int
        :param compute_values: Python dict with the compute service's requirements, dict
        :param name: Name of the service, str
        :param description: Description about the service, str
        """
        if isinstance(service_type, NFTService):
            service = service_type
        else:
            values = copy.deepcopy(compute_values) if compute_values else None
            service = NFTService(
                service_id,
                service_type,
                service_endpoint,
                data_token,
                files,
                timeout,
                values,
                name,
                description,
            )
        logger.debug(
            f"Adding service with service type {service_type} with did {self.did}"
        )
        self._services.append(service)

    def get_service(self, service_type: str) -> Optional[NFTService]:
        """Return a service using."""
        return next(
            (service for service in self._services if service.type == service_type),
            None,
        )
