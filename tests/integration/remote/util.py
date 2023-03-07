#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os
import random
import string
import time
import warnings

from brownie.exceptions import ContractNotFound, TransactionError, VirtualMachineError
from brownie.network import accounts
from enforce_typing import enforce_types
from web3.exceptions import ExtraDataLengthError

from ocean_lib.web3_internal.utils import get_gas_fees

ERRORS_TO_CATCH = (
    ContractNotFound,
    TransactionError,
    ValueError,
    VirtualMachineError,
    ExtraDataLengthError,
)


@enforce_types
def remote_config_mumbai(tmp_path):
    config = {
        "NETWORK_NAME": "polygon-test",
        "METADATA_CACHE_URI": "https://v4.aquarius.oceanprotocol.com",
        "PROVIDER_URL": "https://v4.provider.mumbai.oceanprotocol.com",
        "DOWNLOADS_PATH": "consume-downloads",
    }

    return config


@enforce_types
def remote_config_polygon(tmp_path):
    config = {
        "NETWORK_NAME": "polygon-main",
        "METADATA_CACHE_URI": "https://v4.aquarius.oceanprotocol.com",
        "PROVIDER_URL": "https://v4.provider.polygon.oceanprotocol.com",
        "DOWNLOADS_PATH": "consume-downloads",
    }

    return config


@enforce_types
def get_wallets():
    alice_private_key = os.getenv("REMOTE_TEST_PRIVATE_KEY1")
    bob_private_key = os.getenv("REMOTE_TEST_PRIVATE_KEY2")

    instrs = "You must set it. It must hold Mumbai MATIC."
    assert alice_private_key, f"Need envvar REMOTE_TEST_PRIVATE_KEY1. {instrs}"
    assert bob_private_key, f"Need envvar REMOTE_TEST_PRIVATE_KEY2. {instrs}"

    # wallets
    alice_wallet = accounts.add(alice_private_key)
    bob_wallet = accounts.add(bob_private_key)

    print(f"alice_wallet.address = '{alice_wallet.address}'")
    print(f"bob_wallet.address = '{bob_wallet.address}'")

    return (alice_wallet, bob_wallet)


@enforce_types
def do_nonocean_tx_and_handle_gotchas(ocean, alice_wallet, bob_wallet):
    """Call wallet.transfer(), but handle several gotchas for this test use case:
    - if the test has to repeat, there are nonce errors. Avoid via unique
    - if there are insufficient funds, since they're hard to replace
      automatically in remote testnets, then just skip
    """
    # Simplest possible tx: Alice send Bob some fake MATIC
    bob_eth_before = accounts.at(bob_wallet.address).balance()
    normalized_unixtime = time.time() / 1e9
    amt_send = 1e-8 * (random.random() + normalized_unixtime)

    print("Do a send-Ether tx...")
    try:

        priority_fee, _ = get_gas_fees()
        alice_wallet.transfer(
            bob_wallet.address,
            f"{amt_send:.15f} ether",
            priority_fee=priority_fee,
        )
        bob_eth_after = accounts.at(bob_wallet.address).balance()
    except ERRORS_TO_CATCH as e:
        if error_is_skippable(str(e)):
            warnings.warn(UserWarning(f"Warning: EVM reported error: {e}"))
            return
        raise (e)

    assert bob_eth_after > bob_eth_before
    print("Success")


@enforce_types
def do_ocean_tx_and_handle_gotchas(ocean, alice_wallet):
    """Call create() from data NFT, but handle several gotchas for this test use case:
    - if the test has to repeat, there are nonce errors. Avoid via unique
    - if there are insufficient funds, since they're hard to replace
      automatically in remote testnets, then just skip
    """
    # Alice publish data NFT
    # avoid "replacement transaction underpriced" error: make each tx diff't
    symbol = random_chars()

    print("Call create() from data NFT, and wait for it to complete...")
    num_retries = 2
    while num_retries != 0:
        try:
            priority_fee, max_fee = get_gas_fees()
            data_nft = ocean.data_nft_factory.create(
                {
                    "from": alice_wallet,
                    "priority_fee": priority_fee,
                    "max_fee": max_fee,
                },
                symbol,
                symbol,
            )
            data_nft_symbol = data_nft.symbol()
            break
        except ERRORS_TO_CATCH as e:
            if error_is_skippable(str(e)):
                warnings.warn(UserWarning(f"Warning: EVM reported error: {e}"))
                return
            if "Tx dropped" in str(e):
                num_retries -= 1
                warnings.warn(
                    UserWarning(f"Warning: EVM reported error: {e}\n Retrying...")
                )
                continue
            raise (e)

    assert data_nft_symbol == symbol
    print("Success")


@enforce_types
def error_is_skippable(error_s: str) -> bool:
    return (
        "insufficient funds" in error_s
        or "underpriced" in error_s
        or "No contract deployed at" in error_s
        or "nonce too low" in error_s
        or "Internal error" in error_s
        or "execution reverted" in error_s
        or "No data was returned - the call likely reverted" in error_s
        or "The field extraData is 97 bytes, but should be 32." in error_s
    )


@enforce_types
def random_chars() -> str:
    cand_chars = string.ascii_uppercase + string.digits
    s = "".join(random.choices(cand_chars, k=8)) + str(time.time())
    return s
