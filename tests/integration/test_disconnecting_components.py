#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import threading
import time
from unittest.mock import patch
import requests

from ocean_lib.config import DEFAULT_PROVIDER_URL
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.structures.file_objects import FilesTypeFactory

exception_flag = 0


def _consume(provider_url):
    global exception_flag
    file_url = "https://foo.txt"
    file_dict = {"type": "url", "url": file_url, "method": "GET"}
    file = FilesTypeFactory(file_dict)
    files = [file]

    # Encrypt file objects
    try:
        DataServiceProvider.encrypt(files, provider_url)
    except requests.exceptions.InvalidURL as err:
        exception_flag = 1
        assert err.args[0] == "InvalidURL http://fooprovider.com."


def _iterative_consume(mock):
    for _ in range(5):
        _consume(mock.return_value)
        time.sleep(1)


def _update_with_wrong_provider(mock):
    time.sleep(2)
    mock.return_value = "http://fooprovider.com"


def test_with_wrong_provider(web3, config, publisher_wallet, consumer_wallet, caplog):
    with patch("ocean_lib.config.Config.provider_url") as mock:
        mock.return_value = DEFAULT_PROVIDER_URL
        updating_thread = threading.Thread(
            target=_update_with_wrong_provider,
            args=(mock,),
        )
        updating_thread.start()
        _iterative_consume(mock)
        updating_thread.join()

        assert "Asset urls encrypted successfully" in caplog.text
        assert exception_flag == 1
