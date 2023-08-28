#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import hashlib
from typing import Optional, Union

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
    return Web3.to_checksum_address(address.lower())


@enforce_types
def get_ocean_token_address(config_dict: dict) -> str:
    """Returns the Ocean token address for given network or web3 instance
    Requires either network name or web3 instance.
    """
    addresses = get_contracts_addresses(config_dict)

    return (
        Web3.to_checksum_address(addresses.get("Ocean").lower()) if addresses else None
    )


@enforce_types
def create_checksum(text: str) -> str:
    """
    :return: str
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@enforce_types
def from_wei(amt_wei: int):
    return float(amt_wei / 1e18)


@enforce_types
def to_wei(amt_eth) -> int:
    return int(amt_eth * 1e18)


@enforce_types
def str_with_wei(amt_wei: int) -> str:
    return f"{from_wei(amt_wei)} ({amt_wei} wei)"


@enforce_types
def get_from_address(tx_dict: dict) -> str:
    address = tx_dict["from"].address

    return Web3.to_checksum_address(address.lower())


@enforce_types
def get_args_object(args, kwargs, args_class):
    args_to_use = None
    if args and isinstance(args[0], args_class):
        args_to_use = args[0]
    elif kwargs:
        for key, value in kwargs.items():
            if isinstance(value, args_class):
                args_to_use = value
                break

    if not args_to_use:
        args_to_use = args_class(*args, **kwargs)

    return args_to_use


@enforce_types
def send_ether(
    config, from_wallet, to_address: str, amount: Union[int, float], priority_fee=None
):
    if not Web3.is_checksum_address(to_address):
        to_address = Web3.to_checksum_address(to_address)

    web3 = config["web3_instance"]
    chain_id = web3.eth.chain_id
    tx = {
        "from": from_wallet.address,
        "to": to_address,
        "value": amount,
        "chainId": chain_id,
        "nonce": web3.eth.get_transaction_count(from_wallet.address),
        "type": 2,
    }
    tx["gas"] = web3.eth.estimate_gas(tx)

    if not priority_fee:
        priority_fee = web3.eth.max_priority_fee

    base_fee = web3.eth.get_block("latest")["baseFeePerGas"]

    tx["maxPriorityFeePerGas"] = priority_fee
    tx["maxFeePerGas"] = base_fee * 2 + priority_fee

    signed_tx = web3.eth.account.sign_transaction(tx, from_wallet._private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    return web3.eth.wait_for_transaction_receipt(tx_hash)
