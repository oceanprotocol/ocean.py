#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os
import threading
import time
from unittest.mock import patch

import requests

from ocean_lib.config import DEFAULT_PROVIDER_URL, Config
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.structures.file_objects import FilesTypeFactory
from ocean_lib.web3_internal.constants import ZERO_ADDRESS

exception_flag = 0


def test_with_wrong_provider(config, caplog):
    """Tests encrypt with a good provider URL and then switch to a bad one."""

    with patch("ocean_lib.config.Config.provider_url") as mock:
        mock.return_value = DEFAULT_PROVIDER_URL
        updating_thread = threading.Thread(
            target=_update_with_wrong_component,
            args=(mock,),
        )
        updating_thread.start()
        _iterative_encrypt(mock)
        updating_thread.join()

        assert "Asset urls encrypted successfully" in caplog.text
        assert exception_flag == 1


def test_with_wrong_aquarius(publisher_wallet, caplog, monkeypatch):
    """Tests DDO creation with a good config.ini and then switch to a bad one."""

    updating_thread = threading.Thread(
        target=_update_config_file,
        args=(monkeypatch,),
    )
    config = Config(os.getenv("OCEAN_CONFIG_FILE"))
    ocean = Ocean(config, DataServiceProvider)
    updating_thread.start()
    _iterative_create_ddo(ocean, publisher_wallet)
    updating_thread.join()
    monkeypatch.delenv("OCEAN_CONFIG_FILE")

    assert "Successfully created NFT" in caplog.text
    assert exception_flag == 2


def _create_ddo(ocean, publisher):
    global exception_flag
    metadata = {
        "created": "2020-11-15T12:27:48Z",
        "updated": "2021-05-17T21:58:02Z",
        "description": "Sample description",
        "name": "Sample asset",
        "type": "dataset",
        "author": "OPF",
        "license": "https://market.oceanprotocol.com/terms",
    }
    encrypted_files = _encrypt(DEFAULT_PROVIDER_URL)
    try:
        ocean.assets.create(
            metadata,
            publisher,
            encrypted_files,
            datatoken_templates=[1],
            datatoken_names=["Datatoken 1"],
            datatoken_symbols=["DT1"],
            datatoken_minters=[publisher.address],
            datatoken_fee_managers=[publisher.address],
            datatoken_publish_market_order_fee_addresses=[ZERO_ADDRESS],
            datatoken_publish_market_order_fee_tokens=ocean.OCEAN_address,
            datatoken_publish_market_order_fee_amounts=[0],
            datatoken_bytess=[[b""]],
        )
    except requests.exceptions.SSLError:
        exception_flag = 2


def _iterative_create_ddo(ocean, publisher):
    for _ in range(5):
        _create_ddo(ocean, publisher)
        time.sleep(1)


def _encrypt(provider_url):
    global exception_flag
    file_url = "https://foo.txt"
    file_dict = {"type": "url", "url": file_url, "method": "GET"}
    file = FilesTypeFactory(file_dict)
    files = [file]

    # Encrypt file objects
    try:
        return DataServiceProvider.encrypt(files, provider_url)
    except requests.exceptions.InvalidURL as err:
        exception_flag = 1
        assert err.args[0] == "InvalidURL http://foourl.com."


def _iterative_encrypt(mock):
    for _ in range(5):
        _encrypt(mock.return_value)
        time.sleep(1)


def _update_with_wrong_component(mock):
    time.sleep(2)
    mock.return_value = "http://foourl.com"


def _update_config_file(monkeypatch):
    time.sleep(2)
    monkeypatch.setenv("OCEAN_CONFIG_FILE", "bad-aqua-config.ini")
