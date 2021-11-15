# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import copy
import os
from pathlib import Path
from typing import Optional, Dict, Union

from enforce_typing import enforce_types

from ocean_lib.ocean.util import get_web3
from ocean_lib.services.v4.service import NFTService


@enforce_types
class V4Asset:
    """Asset class to create, import, export, validate Asset/DDO objects for V4."""

    def __init__(
        self,
        did: Optional[str] = None,
        json_text: Optional[str] = None,
        json_filename: Optional[Path] = None,
        metadata: Optional[Dict] = None,
        dictionary: Optional[dict] = None,
    ) -> None:

        self.did = did
        self.version = "4.0.0"
        self.metadata = metadata if metadata else self._build_sample_metadata()
        self.credentials = {}
        self.services = []

        if not json_text and json_filename:
            with open(json_filename, "r") as file_handle:
                json_text = file_handle.read()

        network_url = os.getenv("OCEAN_NETWORK_URL")
        if network_url:
            w3 = get_web3(network_url)
            self.chain_id = w3.eth.chain_id
        else:
            raise TypeError(f"The network URL is not provided.")

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
        # TODO: NFT data
        if self.other_values:
            data.update(self.other_values)

        return data
