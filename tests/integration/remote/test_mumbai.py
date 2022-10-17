#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import random
import warnings

import requests
import time

from .util import get_wallets, random_chars
from ocean_lib.ocean.ocean import Ocean


def test_nonocean_tx(tmp_path):
    """Do a simple non-Ocean tx on Mumbai. Only use Ocean config"""

    # setup
    config = _remote_config_mumbai(tmp_path)
    ocean = Ocean(config)
    (alice_wallet, bob_wallet) = get_wallets(ocean)

    # Get gas price (in Gwei) from Polygon gas station
    gas_station_url = "https://gasstation-mumbai.matic.today/v2"
    gas_price = requests.get(gas_station_url).json()["fast"]["maxFee"]

    # Simplest possible tx: Alice send Bob some fake MATIC
    web3 = ocean.web3
    bob_eth_before = web3.eth.get_balance(bob_wallet.address)
    nonce = web3.eth.getTransactionCount(alice_wallet.address)

    # avoid "replacement transaction underpriced" error: make each tx diff't
    normalized_unixtime = time.time() / 1e9
    amt_send = 1e-8 * (random.random() + normalized_unixtime)
    tx = {
        "nonce": nonce,
        "gasPrice": web3.toWei(gas_price, "gwei"),
        "gas": 21000,  # a standard ETH transfer needs 21K gas
        "chainId": web3.eth.chain_id,
        "to": bob_wallet.address,
        "from": alice_wallet.address,
        "value": web3.toWei(amt_send, "ether"),
    }
    signed_tx = web3.eth.account.sign_transaction(tx, alice_wallet.private_key)

    print("Do a send-Ether tx...")
    try:  # it can get away with "insufficient funds" errors, but not others
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    except ValueError as error:
        if "insufficient funds" in str(error):
            warnings.warn(UserWarning("Warning: Insufficient test MATIC"))
            return
        raise (error)

    print("Wait for send-Ether tx to complete...")
    _ = web3.eth.wait_for_transaction_receipt(tx_hash)

    bob_eth_after = web3.eth.get_balance(bob_wallet.address)
    assert bob_eth_after > bob_eth_before


def test_ocean_tx__create_data_nft(tmp_path):
    """On Mumbai, do a simple Ocean tx: create_data_nft"""

    # setup
    config = _remote_config_mumbai(tmp_path)
    ocean = Ocean(config)
    (alice_wallet, _) = _get_wallets(ocean)

    # Alice publish data NFT
    # avoid "replacement transaction underpriced" error: make each tx diff't
    symbol = random_chars()
    try:  # it can get away with "insufficient funds" errors, but not others
        print("Call create_data_nft(), and wait for it to complete...")
        data_nft = ocean.create_data_nft(symbol, symbol, alice_wallet)

    except ValueError as error:
        if "insufficient funds" in str(error):
            warnings.warn(UserWarning("Warning: Insufficient test MATIC"))
            return
        raise (error)

    assert data_nft.symbol() == symbol
    print("Success")


def _remote_config_mumbai(tmp_path):
    config = {
        "RPC_URL": "https://rpc-mumbai.maticvigil.com",
        "BLOCK_CONFIRMATIONS": 0,
        "TRANSACTION_TIMEOUT": 60,
        "METADATA_CACHE_URI": "https://v4.aquarius.oceanprotocol.com",
        "PROVIDER_URL": "https://v4.provider.mumbai.oceanprotocol.com",
        "DOWNLOADS_PATH": "consume-downloads",
    }

    # -ensure config is truly remote
    assert "mumbai" in config["RPC_URL"]
    assert "oceanprotocol.com" in config["METADATA_CACHE_URI"]
    assert "oceanprotocol.com" in config["PROVIDER_URL"]

    return config
