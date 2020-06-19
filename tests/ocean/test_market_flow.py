#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import os
import time

from ocean_utils.agreements.service_agreement import ServiceAgreement
from ocean_utils.agreements.service_types import ServiceTypes
from ocean_utils.ddo.ddo import DDO

from examples import ExampleConfig
from ocean_lib import ConfigProvider
from tests.resources.helper_functions import (
    get_consumer_account,
    get_publisher_account,
    get_registered_ddo,
    get_publisher_ocean_instance,
    get_consumer_ocean_instance
)


def test_market_flow():
    config = ExampleConfig.get_config()
    ConfigProvider.set_config(config)

    pub_acc = get_publisher_account()

    publisher_ocean_instance = get_publisher_ocean_instance()
    consumer_ocean_instance = get_consumer_ocean_instance()

    # Register ddo
    ddo = get_registered_ddo(publisher_ocean_instance, pub_acc)
    assert isinstance(ddo, DDO)
    assert ddo._other_values['dataTokenAddress']

    cons_ocn = consumer_ocean_instance
    consumer_account = get_consumer_account()
    config = cons_ocn.config

    downloads_path_elements = len(
        os.listdir(config.downloads_path)) if os.path.exists(config.downloads_path) else 0

    # sign agreement using the registered asset did above
    service = ddo.get_service(service_type=ServiceTypes.ASSET_ACCESS)
    sa = ServiceAgreement.from_json(service.as_dictionary())

    dt = publisher_ocean_instance.get_data_token(ddo._other_values['dataTokenAddress'])
    tx_id = dt.mint(pub_acc.address, 100, pub_acc)
    dt.get_tx_receipt(tx_id)
    time.sleep(2)

    def verify_supply(mint_amount=50):
        supply = dt.contract_concise.totalSupply()
        if supply <= 0:
            _tx_id = dt.mint(pub_acc.address, mint_amount, pub_acc)
            dt.get_tx_receipt(_tx_id)
            supply = dt.contract_concise.totalSupply()
        return supply

    while True:
        try:
            s = verify_supply()
            if s > 0:
                break
        except (ValueError, Exception):
            pass

    try:
        tx_id = dt.transfer(consumer_account.address, 10, pub_acc)
        dt.verify_transfer_tx(tx_id, pub_acc.address, consumer_account.address)
    except (AssertionError, Exception) as e:
        print(e)
        raise

    assert cons_ocn.assets.download(
        ddo.did,
        sa.index,
        consumer_account,
        config.downloads_path)

    assert len(os.listdir(config.downloads_path)) == downloads_path_elements + 1
