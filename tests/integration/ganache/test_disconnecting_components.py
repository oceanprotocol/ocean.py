#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import threading
import time

import pytest
import requests

from ocean_lib.data_provider.data_encryptor import DataEncryptor
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.ddo.ddo import DDO
from ocean_lib.example_config import DEFAULT_PROVIDER_URL
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.structures.file_objects import FilesTypeFactory
from ocean_lib.web3_internal.constants import ZERO_ADDRESS

exception_flag = 0


def test_with_wrong_provider(config, caplog):
    """Tests encrypt with a good provider URL and then switch to a bad one."""

    config["PROVIDER_URL"] = DEFAULT_PROVIDER_URL
    updating_thread = threading.Thread(
        target=_update_with_wrong_component,
        args=(config,),
    )
    updating_thread.start()
    _iterative_encrypt(config)
    updating_thread.join()

    assert "DDO urls encrypted successfully" in caplog.text
    assert exception_flag == 1


def test_with_wrong_aquarius(publisher_wallet, caplog, monkeypatch, config):
    """Tests DDO creation with a good config.ini and then switch to a bad one."""
    config["METADATA_CACHE_URI"] = "http:://not-valid-aqua.com"

    with pytest.raises(Exception, match="Invalid or unresponsive aquarius url"):
        ocean = Ocean(config, DataServiceProvider)

    config["METADATA_CACHE_URI"] = "http://172.15.0.5:5000"
    ocean = Ocean(config, DataServiceProvider)

    # force a bad URL, assuming initial Ocean and Aquarius objects were created successfully
    ocean.ddo._aquarius.base_url = "http://not-valid-aqua.com"
    with pytest.raises(Exception):
        ocean.ddo._aquarius.validate_ddo(DDO())


def _create_ddo(ocean, publisher):
    global exception_flag
    metadata = {
        "created": "2020-11-15T12:27:48Z",
        "updated": "2021-05-17T21:58:02Z",
        "description": "Sample description",
        "name": "Sample DDO",
        "type": "dataset",
        "author": "OPF",
        "license": "https://market.oceanprotocol.com/terms",
    }

    file_url = "https://foo.txt"
    file_dict = {"type": "url", "url": file_url, "method": "GET"}
    file = FilesTypeFactory(file_dict)
    files = [file]
    time.sleep(5)
    try:
        ocean.ddo.create(
            metadata,
            publisher,
            files,
            datatoken_templates=[1],
            datatoken_names=["Datatoken 1"],
            datatoken_symbols=["DT1"],
            datatoken_minters=[publisher.address],
            datatoken_fee_managers=[publisher.address],
            datatoken_publish_market_order_fee_addresses=[ZERO_ADDRESS],
            datatoken_publish_market_order_fee_tokens=[ocean.OCEAN_address],
            datatoken_publish_market_order_fee_amounts=[0],
            datatoken_bytess=[[b""]],
        )
    except requests.exceptions.InvalidURL as err:
        exception_flag = 1
        assert err.args[0] == "InvalidURL http://foourl.com."
    except requests.exceptions.ConnectionError as e:
        exception_flag = 2
        assert (
            e.args[0]
            .args[0]
            .startswith("HTTPConnectionPool(host='fooaqua.com', port=80)")
        )


def _iterative_create_ddo(mock_ocean, publisher):
    time.sleep(10)
    _create_ddo(mock_ocean.return_value, publisher)


def _iterative_encrypt(mock):
    global exception_flag
    for _ in range(5):
        try:
            DataEncryptor.encrypt({}, mock["PROVIDER_URL"])
        except requests.exceptions.InvalidURL as err:
            exception_flag = 1
            assert err.args[0] == "InvalidURL http://foourl.com."
        time.sleep(1)


def _update_with_wrong_component(mock):
    time.sleep(2)
    mock["PROVIDER_URL"] = "http://foourl.com"
