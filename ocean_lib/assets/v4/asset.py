# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import copy
import json
import os
from pathlib import Path
from typing import Optional, List

from enforce_typing import enforce_types
from eth_utils import add_0x_prefix

from ocean_lib.assets.credentials import AddressCredential
from ocean_lib.assets.did import did_to_id
from ocean_lib.ocean.util import get_web3
from ocean_lib.services.v4.service import NFTService


@enforce_types
class V4Asset:
    """Asset class to create, import, export, validate Asset/DDO objects for V4."""

    def __init__(
        self,
        did: Optional[str] = None,
        metadata: Optional[dict] = None,
        nft: Optional[dict] = None,
        data_tokens: Optional[dict] = None,
        event: Optional[dict] = None,
        stats: Optional[dict] = None,
        json_text: Optional[str] = None,
        json_filename: Optional[Path] = None,
        dictionary: Optional[dict] = None,
    ) -> None:

        self.did = did
        self.version = "4.0.0"
        self._metadata = metadata if metadata else self._build_sample_metadata()
        self._services = []
        self.credentials = {}
        self.nft = nft
        self.data_tokens = data_tokens
        self.event = event
        self.stats = stats

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
        elif dictionary:
            self._read_dict(dictionary)

    @property
    def asset_id(self) -> Optional[str]:
        """The asset id part of the DID"""
        if not self.did:
            return None
        return add_0x_prefix(did_to_id(self.did))

    @property
    def metadata(self) -> dict:
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

        self.other_values = values

    def _build_sample_metadata(self) -> dict:
        """
        Return a metadata template as a JSON dict.

        :return: dict
        """
        metadata = {
            "created": "2020-11-15T12:27:48Z",
            "updated": "2021-05-17T21:58:02Z",
            "description": "Sample description",
            "name": "Sample asset",
            "type": "dataset",
            "author": "OPF",
            "license": "https://market.oceanprotocol.com/terms",
        }

        return metadata

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
        if self.other_values:
            data.update(self.other_values)

        return data
