#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import os

from ocean_lib.data_provider.data_service_provider import DataServiceProvider


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
