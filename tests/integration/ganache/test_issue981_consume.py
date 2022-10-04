#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import csv
import glob
import os
import shutil

import pytest
from web3 import Web3

from ocean_lib.models.datatoken import Datatoken
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.web3_internal.wallet import Wallet


@pytest.mark.integration
def test1(
    web3: Web3,
    config: dict,
    publisher_wallet: Wallet,
    consumer_wallet: Wallet,
    tmp_path,
):
    ocean = Ocean(config)
    
    url = "https://cexa.oceanprotocol.io/ohlc?exchange=binance&pair=ETH/USDT"
    name = "CEXA ETH-USDT"
    asset = ocean.assets.create_url_asset(name, url, publisher_wallet)
    datatoken_address = asset.datatokens[0]["address"]
    datatoken = Datatoken(ocean.web3, datatoken_address)

    to_address = consumer_wallet.address
    datatoken.mint(to_address, ocean.to_wei(10), publisher_wallet)
    
    order_tx_id = ocean.assets.pay_for_access_service(asset, consumer_wallet)

    #Commented out, we shouldn't need this
    # Initialize service
    #response = data_provider.initialize(
    #    did=asset.did, service=service, consumer_address=consumer_wallet.address
    #)

    # consumer now has access. He downloads the asset.
    # If the connection breaks, consumer can request again by showing order_tx_id.
    file_path = ocean.assets.download_asset(
        asset=asset, consumer_wallet=consumer_wallet, destination=str(tmp_path), order_tx_id=order_tx_id)
    file_name = glob.glob(file_path + "/*")[0]
    print(f"file_path: '{file_path}'")  # e.g. datafile.0xAf07...48,0
    print(f"file_name: '{file_name}'")  # e.g. datafile.0xAf07...48,0/klines?symbol=ETHUSDT?int..22300
    
    #verify that file exists
    assert os.path.exists(file_name), "couldn't find file"

    #load from file into memory
    with open(file_name, "r") as file:
        #data_str is a string holding a list of lists '[[1663113600000,"1574.40000000", ..]]'
        data_str = file.read().rstrip().replace('"', '')
    data = eval(data_str)

    #data is a list of lists
    # -Outer list has one 6 entries; one entry per day.
    # -Inner lists have 12 entries each: Kline open time, Open price, High price, Low price, close Price,  ..
    # -It looks like: [[1662998400000,1706.38,1717.87,1693,1713.56],[1663002000000,1713.56,1729.84,1703.21,1729.08],[1663005600000,1729.08,1733.76,1718.09,1728.83],...

    #Example: get close prices. These can serve as an approximation to spot price
    close_prices = [float(data_at_day[4]) for data_at_day in data]
