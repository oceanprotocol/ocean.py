#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from concurrent.futures import ThreadPoolExecutor

import pytest

from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.example_config import ExampleConfig
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
from ocean_lib.ocean.ocean import Ocean
from tests.resources.ddo_helpers import create_basics
from tests.resources.helper_functions import deploy_erc721_erc20, generate_wallet


def _get_publishing_requirements(ocean: Ocean, wallet, config: dict):
    data_nft, datatoken = deploy_erc721_erc20(config, wallet, wallet)
    data_provider = DataServiceProvider
    _, metadata, files = create_basics(config, data_provider)
    return data_nft, datatoken, metadata, files


def publish_flow(ocean: Ocean, config: dict):
    publisher_wallet = generate_wallet()
    (
        data_nft,
        datatoken,
        metadata,
        files,
    ) = _get_publishing_requirements(ocean, publisher_wallet, config)
    ddo = ocean.assets.create(
        metadata=metadata,
        publisher_wallet=publisher_wallet,
        files=files,
        data_nft_address=data_nft.address,
        deployed_datatokens=[datatoken],
        encrypt_flag=True,
        compress_flag=True,
    )

    assert ddo, "The ddo is not created."
    assert ddo.nft["name"] == "NFT"
    assert ddo.nft["symbol"] == "NFTSYMBOL"
    assert ddo.nft["address"] == data_nft.address
    assert ddo.nft["owner"] == publisher_wallet.address
    assert ddo.datatokens[0]["name"] == "DT1"
    assert ddo.datatokens[0]["symbol"] == "DT1Symbol"
    assert ddo.datatokens[0]["address"] == datatoken.address


def concurrent_publish_flow(concurrent_flows: int, repetitions: int):
    config = ExampleConfig.get_config()
    ocean = Ocean(config)
    mint_fake_OCEAN(config)
    with ThreadPoolExecutor(max_workers=concurrent_flows) as executor:
        for _ in range(concurrent_flows * repetitions):
            executor.submit(publish_flow, ocean, config)


@pytest.mark.slow
@pytest.mark.parametrize(
    ["concurrent_flows", "repetitions"], [(1, 300), (3, 100), (20, 5)]
)
def test_concurrent_publish_flow(concurrent_flows, repetitions):
    concurrent_publish_flow(concurrent_flows, repetitions)
