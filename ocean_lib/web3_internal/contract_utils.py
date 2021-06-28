#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import importlib
import json
import logging
import os
from collections import namedtuple
from decimal import Decimal
from pathlib import Path

import artifacts
from enforce_typing import enforce_types
from eth_account.messages import encode_defunct
from eth_keys import keys
from eth_utils import big_endian_to_int, decode_hex
from jsonsempai import magic  # noqa: F401
from web3 import Web3
from web3.contract import ConciseContract

from ocean_lib.web3_internal.constants import DEFAULT_NETWORK_NAME, NETWORK_NAME_MAP
from ocean_lib.web3_internal.web3_overrides.signature import SignatureFix
from ocean_lib.web3_internal.web3_provider import Web3Provider

Signature = namedtuple("Signature", ("v", "r", "s"))

logger = logging.getLogger(__name__)


def get_contract_definition(contract_name):
    try:
        return importlib.import_module("artifacts." + contract_name).__dict__
    except ModuleNotFoundError:
        raise TypeError("Contract name does not exist in artifacts.")


def load_contract(web3, contract_name, address):
    contract_definition = get_contract_definition(contract_name)
    abi = contract_definition["abi"]
    bytecode = contract_definition["bytecode"]
    contract = web3.eth.contract(address=address, abi=abi, bytecode=bytecode)
    return contract


# Soon to be deprecated
def get_concise_contract(web3, contract_name, address):
    contract_definition = get_contract_definition(contract_name)
    abi = contract_definition["abi"]
    bytecode = contract_definition["bytecode"]
    contract = web3.eth.contract(address=address, abi=abi, bytecode=bytecode)
    return ConciseContract(contract)


def get_contracts_addresses(network, address_file):
    network_alias = {"ganache": "development"}

    if not address_file or not os.path.exists(address_file):
        return None
    with open(address_file) as f:
        addresses = json.load(f)

    network_addresses = addresses.get(network, None)
    if network_addresses is None and network in network_alias:
        network_addresses = addresses.get(network_alias[network], None)

    return network_addresses
