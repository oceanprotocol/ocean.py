#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import importlib
import json
import logging
import os
from typing import Any, Dict, Optional

from enforce_typing import enforce_types
from jsonsempai import magic  # noqa: F401
from web3.contract import Contract
from web3.main import Web3

import artifacts  # noqa

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
def get_contracts_addresses(
    network: str, address_file: str
) -> Optional[Dict[str, str]]:
    """Get addresses for all contract names, per network and address_file given."""
    network_alias = {"ganache": "development"}

    address_file = os.path.expanduser(address_file)
    if not address_file or not os.path.exists(address_file):
        raise Exception("Address file not found.")
    with open(address_file) as f:
        addresses = json.load(f)

    network_addresses = addresses.get(network, None)
    if network_addresses is None and network in network_alias:
        network_addresses = addresses.get(network_alias[network], None)

    if network_addresses is None:
        msg = f" (alias {network_alias[network]})" if network in network_alias else ""
        raise Exception(
            f"Address not found for {network}{msg}. Please check your address file."
        )

    return _checksum_contract_addresses(network_addresses=network_addresses)


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
