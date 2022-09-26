#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os

import pytest
import requests

from ocean_lib.ocean.ocean import Ocean
from ocean_lib.web3_internal.constants import GAS_LIMIT_DEFAULT
from ocean_lib.web3_internal.wallet import Wallet


def test_nonocean_tx(tmp_path):
    """Do a simple non-Ocean tx on Mumbai. Only use Ocean config"""

    # setup
    config = _remote_config(tmp_path)
    ocean = Ocean(config)
    (alice_wallet, bob_wallet) = _get_wallets(ocean)

    # Get gas price (in Gwei) from Polygon gas station
    gas_price = requests.get("https://gasstation-mumbai.matic.today/v2").json()["fast"][
        "maxFee"
    ]

    # Simplest possible tx: Alice send Bob some fake MATIC
    web3 = ocean.web3
    bob_eth_before = web3.eth.get_balance(bob_wallet.address)
    nonce = web3.eth.getTransactionCount(alice_wallet.address)
    tx = {
        "nonce": nonce,
        "gasPrice": web3.toWei(gas_price, "gwei"),
        "gas": 21000,  # a standard ETH transfer needs 21K gas
        "chainId": web3.eth.chain_id,
        "to": bob_wallet.address,
        "from": alice_wallet.address,
        "value": web3.toWei(0.001, "ether"),
    }
    signed_tx = web3.eth.account.sign_transaction(tx, alice_wallet.private_key)

    print("Do a send-Ether tx...")
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)

    print("Wait for send-Ether tx to complete...")
    _ = web3.eth.wait_for_transaction_receipt(tx_hash)

    bob_eth_after = web3.eth.get_balance(bob_wallet.address)
    assert bob_eth_after > bob_eth_before


@pytest.mark.skip(reason="Don't skip, once fixed #943")
def test_ocean_tx(tmp_path):
    """Do a (simple) Ocean tx on Mumbai"""

    # setup
    config = _remote_config(tmp_path)
    ocean = Ocean(config)
    (alice_wallet, _) = _get_wallets(ocean)

    # Alice publish data NFT
    print("Do an Ocean tx, and wait for it to complete...")
    data_nft = ocean.create_data_nft("My NFT1", "NFT1", alice_wallet)
    assert data_nft.symbol() == "NFT1"


def _get_wallets(ocean):
    config, web3 = ocean.config_dict, ocean.web3

    alice_private_key = os.getenv("REMOTE_TEST_PRIVATE_KEY1")
    bob_private_key = os.getenv("REMOTE_TEST_PRIVATE_KEY2")

    instrs = "You must set it. It must hold Mumbai MATIC."
    assert (
        alice_private_key is not None
    ), f"Need envvar REMOTE_TEST_PRIVATE_KEY1. {instrs}"
    assert (
        bob_private_key is not None
    ), f"Need envvar REMOTE_TEST_PRIVATE_KEY2. {instrs}"

    # wallets
    alice_wallet = Wallet(
        web3,
        alice_private_key,
        config["BLOCK_CONFIRMATIONS"],
        config["TRANSACTION_TIMEOUT"],
    )
    bob_wallet = Wallet(
        web3,
        bob_private_key,
        config["BLOCK_CONFIRMATIONS"],
        config["TRANSACTION_TIMEOUT"],
    )
    print(f"alice_wallet.address = '{alice_wallet.address}'")
    print(f"bob_wallet.address = '{bob_wallet.address}'")

    return (alice_wallet, bob_wallet)


def _remote_config(tmp_path):
    config = {
        "OCEAN_NETWORK_URL": "https://rpc-mumbai.maticvigil.com",
        "ADDRESS_FILE": "~/.ocean/ocean-contracts/artifacts/address.json",
        "BLOCK_CONFIRMATIONS": 0,
        "TRANSACTION_TIMEOUT": 60,
        "METADATA_CACHE_URI": "https://v4.aquarius.oceanprotocol.com",
        "PROVIDER_URL": "https://v4.provider.mumbai.oceanprotocol.com",
        "GAS_LIMIT": GAS_LIMIT_DEFAULT,
        "CHAIN_ID": 80001,
        "DOWNLOADS_PATH": "consume-downloads",
    }

    # -ensure config is truly remote
    assert "mumbai" in config["OCEAN_NETWORK_URL"]
    assert "oceanprotocol.com" in config["METADATA_CACHE_URI"]
    assert "oceanprotocol.com" in config["PROVIDER_URL"]

    return config
