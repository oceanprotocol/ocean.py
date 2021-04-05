#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import os

from ocean_lib.data_provider.data_service_provider import DataServiceProvider, logger
from ocean_utils.agreements.service_types import ServiceTypes
from ocean_utils.http_requests.requests_session import get_requests_session


class DataProviderMock(object):
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
    def restart_compute_job(*args, **kwargs):
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
    def get_url(config):
        return DataServiceProvider.get_url(config)

    @staticmethod
    def build_download_endpoint(provider_uri=None):
        service_name = "download"
        provider_uri = "http://localhost:8030"
        return "GET", f"{provider_uri}/api/v1/services/{service_name}"

    @staticmethod
    def download_service(
        did,
        service_endpoint,
        wallet,
        files,
        destination_folder,
        service_id,
        token_address,
        order_tx_id,
        index=None,
    ):

        indexes = range(len(files))
        if index is not None:
            assert isinstance(index, int), logger.error("index has to be an integer.")
            assert index >= 0, logger.error("index has to be 0 or a positive integer.")
            assert index < len(files), logger.error(
                "index can not be bigger than the number of files"
            )
            indexes = [index]

        base_url = (
            f"{service_endpoint}"
            f"?documentId={did}"
            f"&serviceId={service_id}"
            f"&serviceType={ServiceTypes.ASSET_ACCESS}"
            f"&dataToken={token_address}"
            f"&transferTxId={order_tx_id}"
            f"&consumerAddress={wallet.address}"
        )
        provider_uri = DataProviderMock.build_download_endpoint(service_endpoint)[1]
        for i in indexes:
            signature = DataServiceProvider.sign_message(
                wallet, did, provider_uri=provider_uri
            )
            download_url = base_url + f"&signature={signature}&fileIndex={i}"
            logger.info(f"invoke consume endpoint with this url: {download_url}")
            http_client = get_requests_session()
            response = http_client.get(download_url, stream=True)
            file_name = DataServiceProvider._get_file_name(response)
            DataServiceProvider.write_file(
                response, destination_folder, file_name or f"file-{i}"
            )
