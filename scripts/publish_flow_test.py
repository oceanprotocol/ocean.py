#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os

import pytest

from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.example_config import ExampleConfig
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.wallet import Wallet
from tests.resources.ddo_helpers import build_credentials_dict, create_basics
from tests.resources.helper_functions import deploy_erc721_erc20, get_address_of_type


@pytest.mark.slow
def test_stressed_publish():
    config = ExampleConfig.get_config()
    ocean = Ocean(config)

    # Create Alice's wallet
    alice_private_key = os.getenv("TEST_PRIVATE_KEY1")
    alice_wallet = Wallet(
        ocean.web3,
        alice_private_key,
        config.block_confirmations,
        config.transaction_timeout,
    )
    assert alice_wallet.address

    # Mint OCEAN
    mint_fake_OCEAN(config)
    assert alice_wallet.web3.eth.get_balance(alice_wallet.address) > 0, "need ETH"

    for _ in range(1000):
        erc721_nft, erc20_token = deploy_erc721_erc20(
            ocean.web3, config, alice_wallet, alice_wallet
        )
        data_provider = DataServiceProvider
        _, metadata, encrypted_files = create_basics(config, ocean.web3, data_provider)

        # Send 1000 requests to Aquarius for creating a plain asset with ERC20 data
        ddo = ocean.assets.create(
            metadata=metadata,
            publisher_wallet=alice_wallet,
            encrypted_files=encrypted_files,
            erc721_address=erc721_nft.address,
            erc20_templates=[1],
            erc20_names=["Datatoken 1"],
            erc20_symbols=["DT1"],
            erc20_minters=[alice_wallet.address],
            erc20_fee_managers=[alice_wallet.address],
            erc20_publish_market_addresses=[ZERO_ADDRESS],
            erc20_publish_market_fee_tokens=[get_address_of_type(config, "Ocean")],
            erc20_caps=[ocean.to_wei("0.5")],
            erc20_publish_market_fee_amounts=[0],
            erc20_bytess=[[b""]],
        )
        assert ddo, "The asset is not created."
        assert ddo.nft["name"] == "NFT"
        assert ddo.nft["symbol"] == "NFTSYMBOL"
        assert ddo.nft["address"] == erc721_nft.address
        assert ddo.nft["owner"] == alice_wallet.address
        assert ddo.datatokens[0]["name"] == "Datatoken 1"
        assert ddo.datatokens[0]["symbol"] == "DT1"
        assert ddo.credentials == build_credentials_dict()

    # Send 1000 requests to Aquarius for creating a plain asset
    for _ in range(1000):
        erc721_nft, erc20_token = deploy_erc721_erc20(
            ocean.web3, config, alice_wallet, alice_wallet
        )
        data_provider = DataServiceProvider
        _, metadata, encrypted_files = create_basics(config, ocean.web3, data_provider)

        asset = ocean.assets.create(
            metadata,
            alice_wallet,
            encrypted_files,
            erc721_address=erc721_nft.address,
            deployed_erc20_tokens=[erc20_token],
        )
        assert asset
        assert asset.nft["name"] == "NFT"
        assert asset.nft["symbol"] == "NFTSYMBOL"
        assert asset.nft["address"] == erc721_nft.address
        assert asset.nft["owner"] == alice_wallet.address
        assert asset.datatokens[0]["name"] == "ERC20DT1"
        assert asset.datatokens[0]["symbol"] == "ERC20DT1Symbol"

    # Send 1000 requests to Aquarius for creating an encrypted asset
    for _ in range(1000):
        erc721_nft, erc20_token = deploy_erc721_erc20(
            ocean.web3, config, alice_wallet, alice_wallet
        )
        data_provider = DataServiceProvider
        _, metadata, encrypted_files = create_basics(config, ocean.web3, data_provider)
        asset = ocean.assets.create(
            metadata=metadata,
            publisher_wallet=alice_wallet,
            encrypted_files=encrypted_files,
            erc721_address=erc721_nft.address,
            deployed_erc20_tokens=[erc20_token],
            encrypt_flag=True,
        )
        assert asset, "The asset is not created."
        assert asset.nft["name"] == "NFT"
        assert asset.nft["symbol"] == "NFTSYMBOL"
        assert asset.nft["address"] == erc721_nft.address
        assert asset.nft["owner"] == alice_wallet.address
        assert asset.datatokens[0]["name"] == "ERC20DT1"
        assert asset.datatokens[0]["symbol"] == "ERC20DT1Symbol"
        assert asset.datatokens[0]["address"] == erc20_token.address

    # Send 1000 requests to Aquarius for creating a compressed asset
    for _ in range(1000):
        erc721_nft, erc20_token = deploy_erc721_erc20(
            ocean.web3, config, alice_wallet, alice_wallet
        )
        data_provider = DataServiceProvider
        _, metadata, encrypted_files = create_basics(config, ocean.web3, data_provider)
        ddo = ocean.assets.create(
            metadata=metadata,
            publisher_wallet=alice_wallet,
            encrypted_files=encrypted_files,
            erc721_address=erc721_nft.address,
            deployed_erc20_tokens=[erc20_token],
            compress_flag=True,
        )
        assert ddo, "The asset is not created."
        assert ddo.nft["name"] == "NFT"
        assert ddo.nft["symbol"] == "NFTSYMBOL"
        assert ddo.nft["address"] == erc721_nft.address
        assert ddo.nft["owner"] == alice_wallet.address
        assert ddo.datatokens[0]["name"] == "ERC20DT1"
        assert ddo.datatokens[0]["symbol"] == "ERC20DT1Symbol"
        assert ddo.datatokens[0]["address"] == erc20_token.address
