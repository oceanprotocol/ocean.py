#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from concurrent.futures import ThreadPoolExecutor

import pytest

from ocean_lib.config import Config
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.example_config import ExampleConfig
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.web3_internal.wallet import Wallet
from tests.resources.ddo_helpers import create_basics
from tests.resources.helper_functions import deploy_erc721_erc20, generate_wallet


def _get_publishing_requirements(ocean: Ocean, wallet: Wallet, config: Config):
    erc721_nft, erc20_token = deploy_erc721_erc20(ocean.web3, config, wallet, wallet)
    data_provider = DataServiceProvider
    _, metadata, encrypted_files = create_basics(config, ocean.web3, data_provider)
    return erc721_nft, erc20_token, metadata, encrypted_files


def concurrent_publish_flow(concurrent_flows: int, duration: int):
    config = ExampleConfig.get_config()
    ocean = Ocean(config)
    mint_fake_OCEAN(config)
    with ThreadPoolExecutor(max_workers=concurrent_flows) as executor:
        for _ in range(concurrent_flows * duration):
            executor.submit(publish_flow, ocean, config)


def publish_flow(ocean: Ocean, config: Config):
    wallet = generate_wallet()
    (
        erc721_nft,
        erc20_token,
        metadata,
        encrypted_files,
    ) = _get_publishing_requirements(ocean, wallet, config)
    asset = ocean.assets.create(
        metadata=metadata,
        publisher_wallet=wallet,
        encrypted_files=encrypted_files,
        erc721_address=erc721_nft.address,
        deployed_erc20_tokens=[erc20_token],
        encrypt_flag=True,
        compress_flag=True,
    )

    assert asset, "The asset is not created."
    assert asset.nft["name"] == "NFT"
    assert asset.nft["symbol"] == "NFTSYMBOL"
    assert asset.nft["address"] == erc721_nft.address
    assert asset.nft["owner"] == wallet.address
    assert asset.datatokens[0]["name"] == "ERC20DT1"
    assert asset.datatokens[0]["symbol"] == "ERC20DT1Symbol"
    assert asset.datatokens[0]["address"] == erc20_token.address


@pytest.mark.slow
def test_concurrent_pool_creation():
    concurrent_flows_values = [1, 3, 20]
    reps = [3000, 1000, 50]
    for counter in range(len(concurrent_flows_values)):
        concurrent_publish_flow(concurrent_flows_values[counter], reps[counter])
