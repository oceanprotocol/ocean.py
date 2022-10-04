#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import Optional

from enforce_typing import enforce_types
from web3.main import Web3

from ocean_lib.web3_internal.contract_utils import get_contracts_addresses

GANACHE_URL = "http://127.0.0.1:8545"


@enforce_types
def get_address_of_type(
    config_dict: dict, address_type: str, key: Optional[str] = None
) -> str:
    addresses = get_contracts_addresses(config_dict)
    if address_type not in addresses.keys():
        raise KeyError(f"{address_type} address is not set in the config file")
    address = (
        addresses[address_type]
        if not isinstance(addresses[address_type], dict)
        else addresses[address_type].get(key, addresses[address_type]["1"])
    )
    return Web3.toChecksumAddress(address.lower())


@enforce_types
def get_ocean_token_address(config_dict: dict) -> str:
    """Returns the Ocean token address for given network or web3 instance
    Requires either network name or web3 instance.
    """
    addresses = get_contracts_addresses(config_dict)

    return Web3.toChecksumAddress(addresses.get("Ocean").lower()) if addresses else None
