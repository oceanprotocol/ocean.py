#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import json
import os
from pathlib import Path
from typing import Union, Optional, Dict

from ocean_lib.http_requests.requests_session import get_requests_session
from ocean_lib.data_provider.data_service_provider import DataServiceProvider, logger
from requests.models import PreparedRequest

from ocean_lib.web3_internal.wallet import Wallet


class DataProviderMock(DataServiceProvider):
    def __init__(self, ocean_instance=None, wallet=None):
        """Initialises DataProviderMock object."""
        if not ocean_instance:
            from tests.resources.helper_functions import get_publisher_ocean_instance

            ocean_instance = get_publisher_ocean_instance(use_provider_mock=True)

        self.ocean_instance = ocean_instance
        self.wallet = wallet
        if not wallet:
            from tests.resources.helper_functions import get_publisher_wallet

            self.wallet = get_publisher_wallet()

    @staticmethod
    def consume_service(
        did, service_endpoint, wallet_address, files, destination_folder, *_, **__
    ):
        for f in files:
            with open(
                os.path.join(destination_folder, os.path.basename(f["url"])), "w"
            ) as of:
                of.write(f"mock data {did}.{service_endpoint}.{wallet_address}")

    @staticmethod
    def start_compute_job(*args, **kwargs):
        return True

    @staticmethod
    def stop_compute_job(*args, **kwargs):
        return True

    @staticmethod
    def delete_compute_job(*args, **kwargs):
        return True

    @staticmethod
    def compute_job_status(*args, **kwargs):
        return True

    @staticmethod
    def compute_job_result(*args, **kwargs):
        return True

    @staticmethod
    def compute_job_result_file(*args, **kwargs):
        return True

    @staticmethod
    def get_url(config):
        return DataServiceProvider.get_url(config)

    @staticmethod
    def build_download_endpoint(provider_uri=None):
        service_name = "download"
        provider_uri = "http://localhost:8030"
        return "GET", f"{provider_uri}/api/v1/services/{service_name}"

    @staticmethod
    def initialize(
        did: str,
        service_id: str,
        file_index: int,
        consumer_address: str,
        service_endpoint: str,
        userdata: Optional[Dict] = None,
    ):
        initialize_endpoint = service_endpoint
        initialize_endpoint += f"?documentId={did}"
        initialize_endpoint += f"&serviceId={service_id}"
        initialize_endpoint += f"&fileIndex={file_index}"
        initialize_endpoint += f"&consumerAddress={consumer_address}"
        if userdata:
            initialize_endpoint += f"&userdata={json.dumps(userdata)}"
        DataServiceProvider._http_method("get", initialize_endpoint)

    @staticmethod
    def download(
        did: str,
        service_id: str,
        tx_id: str,
        file_index: int,
        consumer_wallet: Wallet,
        download_endpoint: str,
        destination_folder: Union[str, Path],
        userdata: Optional[Dict] = None,
    ):

        payload = {
            "documentId": did,
            "serviceId": service_id,
            "consumerAddress": consumer_wallet.address,
            "transferTxId": tx_id,
            "fileIndex": file_index,
        }

        if userdata:
            userdata = json.dumps(userdata)
            payload["userdata"] = userdata

        payload["nonce"], payload["signature"] = DataServiceProvider.sign_message(
            consumer_wallet, did
        )
        req = PreparedRequest()
        req.prepare_url(download_endpoint, payload)
        base_url = req.url

        download_url = (
            base_url + f"&signature={payload['signature']}&fileIndex={file_index}"
        )
        logger.info(f"invoke consume endpoint with this url: {download_url}")
        http_client = get_requests_session()
        response = http_client.get(download_url, stream=True)
        response.status_code = 200

        DataServiceProvider.write_file(response, destination_folder, "foo_file.txt")
