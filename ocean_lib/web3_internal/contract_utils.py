#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import importlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from enforce_typing import enforce_types
from jsonsempai import magic  # noqa: F401
from addresses import address as contract_addresses  # noqa: F401
from web3.contract import Contract
from web3.main import Web3

import artifacts  # noqa

from ocean_lib.utils.utilities import get_chain_id_from_url

logger = logging.getLogger(__name__)


@enforce_types
def get_contract_definition(contract_name: str) -> Dict[str, Any]:
    """Returns the abi JSON for a contract name."""
    try:
        return importlib.import_module("artifacts." + contract_name).__dict__
    except ModuleNotFoundError:
        raise TypeError("Contract name does not exist in artifacts.")


@enforce_types
def load_contract(web3: Web3, contract_name: str, address: Optional[str]) -> Contract:
    """Loads a contract using its name and address."""
    contract_definition = get_contract_definition(contract_name)
    abi = contract_definition["abi"]
    bytecode = contract_definition["bytecode"]
    contract = web3.eth.contract(address=address, abi=abi, bytecode=bytecode)
    return contract


@enforce_types
def get_addresses_with_fallback(config):
    address_file = config.get("ADDRESS_FILE")
    address_file = (
        os.path.expanduser(address_file)
        if address_file
        else Path(contract_addresses.__file__).expanduser().resolve()
    )

    if not address_file or not os.path.exists(address_file):
        raise Exception("Address file not found.")
    with open(address_file) as f:
        addresses = json.load(f)

    return addresses


@enforce_types
def get_contracts_addresses(config) -> Optional[Dict[str, str]]:
    """Get addresses for all contract names, per network and address_file given."""

    chain_id = get_chain_id_from_url(config["RPC_URL"])
    addresses = get_addresses_with_fallback(config)

    network_addresses = [
        val for key, val in addresses.items() if val["chainId"] == chain_id
    ]

    if network_addresses is None:
        raise Exception(
            f"Address not found for {chain_id}. Please check your address file."
        )

    return _checksum_contract_addresses(network_addresses=network_addresses[0])


@enforce_types
# Check singnet/snet-cli#142 (comment). You need to provide a lowercase address then call web3.toChecksumAddress()
# for software safety.
def _checksum_contract_addresses(
    network_addresses: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    for key, value in network_addresses.items():
        if key == "chainId":
            continue
        if isinstance(value, int):
            continue
        if isinstance(value, dict):
            for k, v in value.items():
                value.update({k: Web3.toChecksumAddress(v.lower())})
        else:
            network_addresses.update({key: Web3.toChecksumAddress(value.lower())})

    return network_addresses
