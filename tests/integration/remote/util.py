#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os
import random
import string
import time
import warnings

from brownie.exceptions import VirtualMachineError
from brownie.network import accounts, chain, priority_fee


def remote_config_mumbai(tmp_path):
    config = {
        "NETWORK_NAME": "mumbai",
        "METADATA_CACHE_URI": "https://v4.aquarius.oceanprotocol.com",
        "PROVIDER_URL": "https://v4.provider.mumbai.oceanprotocol.com",
        "DOWNLOADS_PATH": "consume-downloads",
    }

    return config


def remote_config_polygon(tmp_path):
    config = {
        "NETWORK_NAME": "polygon",
        "METADATA_CACHE_URI": "https://v4.aquarius.oceanprotocol.com",
        "PROVIDER_URL": "https://v4.provider.polygon.oceanprotocol.com",
        "DOWNLOADS_PATH": "consume-downloads",
    }

    return config


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


def set_aggressive_gas_fees():
    # Polygon & Mumbai uses EIP-1559. So, dynamically determine priority fee
    priority_fee(chain.priority_fee)


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
    try:  # it can get away with some errors, but not others
        alice_wallet.transfer(bob_wallet.address, f"{amt_send:.15f} ether")
    except (ValueError, VirtualMachineError) as e:
        if "insufficient funds" in str(e) or "underpriced" in str(e):
            warnings.warn(UserWarning("Warning: EVM reported error: {error}"))
            return
        raise (e)

    bob_eth_after = accounts.at(bob_wallet.address).balance()
    assert bob_eth_after > bob_eth_before


def do_ocean_tx_and_handle_gotchas(ocean, alice_wallet):
    """Call create_data_nft(), but handle several gotchas for this test use case:
    - if the test has to repeat, there are nonce errors. Avoid via unique
    - if there are insufficient funds, since they're hard to replace
      automatically in remote testnets, then just skip
    """
    # Alice publish data NFT
    # avoid "replacement transaction underpriced" error: make each tx diff't
    symbol = random_chars()
    try:  # it can get away with some errors, but not others
        print("Call create_data_nft(), and wait for it to complete...")
        data_nft = ocean.create_data_nft(symbol, symbol, alice_wallet)

    except (ValueError, VirtualMachineError) as e:
        if "insufficient funds" in str(e) or "underpriced" in str(e):
            warnings.warn(UserWarning("Warning: EVM reported error: {error}"))
            return
        raise (e)

    assert data_nft.symbol() == symbol
    print("Success")


def random_chars() -> str:
    cand_chars = string.ascii_uppercase + string.digits
    s = "".join(random.choices(cand_chars, k=8)) + str(time.time())
    return s
