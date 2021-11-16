# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import copy
import json
import os
from pathlib import Path
from typing import Optional

from enforce_typing import enforce_types

from ocean_lib.ocean.util import get_web3
from ocean_lib.services.v4.service import NFTService


@enforce_types
class V4Asset:
    """Asset class to create, import, export, validate Asset/DDO objects for V4."""

    def __init__(
        self,
        did: str,
        nft: dict,
        data_tokens: dict,
        event: dict,
        stats: dict,
        metadata: Optional[dict] = None,
        json_text: Optional[str] = None,
        json_filename: Optional[Path] = None,
        dictionary: Optional[dict] = None,
    ) -> None:

        self.did = did
        self.version = "4.0.0"
        self.metadata = metadata if metadata else self._build_sample_metadata()
        self.services = []
        self.credentials = {}
        self.nft = nft
        self.data_tokens = data_tokens
        self.event = event
        self.stats = stats

        if not json_text and json_filename:
            with open(json_filename, "r") as file_handle:
                json_text = file_handle.read()
        if json_text:
            self._read_dict(json.loads(json_text))
        elif dictionary:
            self._read_dict(dictionary)

        network_url = os.getenv("OCEAN_NETWORK_URL")
        if network_url:
            w3 = get_web3(network_url)
            self.chain_id = w3.eth.chain_id
        else:
            raise TypeError(f"The network URL is not provided.")

    def _read_dict(self, dictionary: dict) -> None:
        """Import a JSON dict into this Asset."""
        values = copy.deepcopy(dictionary)
        id_key = "id" if "id" in values else "_id"
        self.did = values.pop(id_key)
        self.chain_id = values.pop("chainId")

        if "metadata" in values:
            self.metadata = values.pop("metadata")
        if "services" in values:
            self.services = []
            for value in values.pop("services"):
                if isinstance(value, str):
                    value = json.loads(value)

                service = NFTService.from_json(value)
                self.services.append(service)
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

        data["metadata"] = self.metadata

        if self.services:
            data["service"] = [service.as_dictionary() for service in self.services]
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
