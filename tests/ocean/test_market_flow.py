#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import os

from ocean_utils.agreements.service_types import ServiceTypes

from examples import ExampleConfig
from ocean_lib import ConfigProvider
from ocean_lib.ocean.util import toBase18
from ocean_lib.assets.asset import Asset
from ocean_lib.assets.service_agreement import ServiceAgreement
from tests.resources.helper_functions import (
    get_consumer_wallet,
    get_publisher_wallet,
    get_registered_ddo,
    get_publisher_ocean_instance,
    get_consumer_ocean_instance,
    get_web3
)


def test_market_flow():
    config = ExampleConfig.get_config()
    ConfigProvider.set_config(config)

    web3 = get_web3()
    pub_wallet = get_publisher_wallet()

    publisher_ocean = get_publisher_ocean_instance()
    consumer_ocean = get_consumer_ocean_instance()

    # Register Asset
    asset = get_registered_ddo(publisher_ocean, pub_wallet)
    assert isinstance(asset, Asset)
    assert asset.data_token_address

    consumer_wallet = get_consumer_wallet()
    downloads_path = consumer_ocean.config.downloads_path

    downloads_path_elements = len(
        os.listdir(downloads_path)) if os.path.exists(downloads_path) else 0

    # sign agreement using the registered asset did above
    service = asset.get_service(service_type=ServiceTypes.ASSET_ACCESS)
    sa = ServiceAgreement.from_json(service.as_dictionary())

    dt = publisher_ocean.get_data_token(asset.data_token_address)
    dt.mint(pub_wallet.address, toBase18(100.0), pub_wallet)

    dt.transfer(consumer_wallet.address, toBase18(10.0), pub_wallet)
    
    assert consumer_ocean.assets.download(
        asset.did,
        sa.index,
        consumer_wallet.account,
        downloads_path)

    assert len(os.listdir(downloads_path)) == downloads_path_elements + 1
