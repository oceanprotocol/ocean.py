#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import glob
import os
from datetime import datetime, timedelta

import pytest
from web3.main import Web3

from ocean_lib.agreements.service_types import ServiceTypes
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.ocean.ocean import Ocean
from tests.resources.ddo_helpers import get_first_service_by_type


@pytest.mark.integration
def test1(
    config: dict,
    publisher_wallet,
    consumer_wallet,
    tmp_path,
):
    data_provider = DataServiceProvider
    ocean = Ocean(config)

    # Publish
    end_datetime = datetime.now()
    start_datetime = end_datetime - timedelta(days=7)  # the previous week
    url = f"https://api.binance.com/api/v3/klines?symbol=ETHUSDT&interval=1d&startTime={int(start_datetime.timestamp())*1000}&endTime={int(end_datetime.timestamp())*1000}"
    name = "Binance ETH-USDT"
    (data_nft, datatoken, ddo) = ocean.assets.create_url_asset(
        name, url, publisher_wallet
    )

    # Initialize service
    service = get_first_service_by_type(ddo, ServiceTypes.ASSET_ACCESS)
    data_provider.initialize(
        did=ddo.did, service=service, consumer_address=consumer_wallet.address
    )

    # Share access
    to_address = consumer_wallet.address
    datatoken.mint(to_address, Web3.toWei(10, "ether"), {"from": publisher_wallet})

    # Consume
    destination = str(tmp_path)
    order_tx_id = ocean.assets.pay_for_access_service(ddo, consumer_wallet)
    file_path = ocean.assets.download_asset(
        ddo,
        consumer_wallet,
        destination,
        order_tx_id,
    )
    file_name = glob.glob(file_path + "/*")[0]
    print(f"file_path: '{file_path}'")  # e.g. datafile.0xAf07...48,0
    print(
        f"file_name: '{file_name}'"
    )  # e.g. datafile.0xAf07...48,0/klines?symbol=ETHUSDT?int..22300

    # verify that file exists
    assert os.path.exists(file_name), "couldn't find file"

    # load from file into memory
    with open(file_name, "r") as file:
        # data_str is a string holding a list of lists '[[1663113600000,"1574.40000000", ..]]'
        data_str = file.read().rstrip().replace('"', "")

    data = eval(data_str)

    # data is a list of lists
    # -Outer list has one 6 entries; one entry per day.
    # -Inner lists have 12 entries each: Kline open time, Open price, High price, Low price, close Price,  ..
    # -It looks like: [[1662998400000,1706.38,1717.87,1693,1713.56],[1663002000000,1713.56,1729.84,1703.21,1729.08],[1663005600000,1729.08,1733.76,1718.09,1728.83],...

    # Example: get close prices. These can serve as an approximation to spot price
    close_prices = [float(data_at_day[4]) for data_at_day in data]
    assert close_prices
