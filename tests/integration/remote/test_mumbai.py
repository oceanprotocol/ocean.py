#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import warnings

from ocean_lib.ocean.ocean import Ocean
from ocean_lib.web3_internal.transactions import send_ether

from .util import get_wallets, random_chars


def test_nonocean_tx(tmp_path):
    """Do a simple non-Ocean tx on Mumbai. Only use Ocean config"""

    # setup
    config = _remote_config_mumbai(tmp_path)
    ocean = Ocean(config)
    (alice_wallet, bob_wallet) = get_wallets(ocean)

    # Simplest possible tx: Alice send Bob some fake MATIC
    # TODO: replace with send_ether?
    web3 = ocean.web3
    bob_eth_before = web3.eth.get_balance(bob_wallet.address)

    print("Do a send-Ether tx...")
    try:  # it can get away with "insufficient funds" errors, but not others
        send_ether(config, alice_wallet, bob_wallet.address, "0.0001 ether")
    except ValueError as error:
        if "insufficient funds" in str(error):
            warnings.warn(UserWarning("Warning: Insufficient test MATIC"))
            return
        raise (error)

    bob_eth_after = web3.eth.get_balance(bob_wallet.address)
    assert bob_eth_after > bob_eth_before


def test_ocean_tx__create_data_nft(tmp_path):
    """On Mumbai, do a simple Ocean tx: create_data_nft"""

    # setup
    config = _remote_config_mumbai(tmp_path)
    ocean = Ocean(config)
    (alice_wallet, _) = get_wallets(ocean)

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
