#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import os
import re

from ocean_lib.config_provider import ConfigProvider
from ocean_lib.data_provider.data_service_provider import DataServiceProvider, logger
from ocean_utils.agreements.service_types import ServiceTypes


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
    def get_consume_endpoint(config):
        return f"{DataServiceProvider.get_download_endpoint(config)}"

    @staticmethod
    def get_compute_endpoint(config):
        return f"{DataServiceProvider.get_compute_endpoint(config)}"

    @staticmethod
    def get_download_endpoint(config):
        return f"{DataServiceProvider.get_download_endpoint(config)}"

    @staticmethod
    def build_download_endpoint(service_name):
        service_name = "download"
        provider_uri = "http://localhost:8030"
        return "GET", f"{provider_uri}/services/{service_name}"

    @staticmethod
    def _get_file_name(response):
        try:
            return re.match(
                r"attachment;filename=(.+)", response.headers.get("content-disposition")
            )[1]
        except Exception as e:
            logger.warning(f"It was not possible to get the file name. {e}")

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
        config = ConfigProvider.get_config()

        for i in indexes:
            signature = DataServiceProvider.sign_message(wallet, did, config)
            download_url = base_url + f"&signature={signature}&fileIndex={i}"
            logger.info(f"invoke consume endpoint with this url: {download_url}")
            response = DataServiceProvider.get_http_client().get(
                download_url, stream=True
            )
            file_name = DataProviderMock._get_file_name(response)
            DataServiceProvider.write_file(
                response, destination_folder, file_name or f"file-{i}"
            )

        return True
