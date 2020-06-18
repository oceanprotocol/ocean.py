#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import os

from squid_py.data_provider.data_service_provider import DataServiceProvider


class DataProviderMock(object):
    def __init__(self, ocean_instance=None, account=None):
        if not ocean_instance:
            from tests.resources.helper_functions import get_publisher_ocean_instance
            ocean_instance = get_publisher_ocean_instance(
                use_provider_mock=True
            )

        self.ocean_instance = ocean_instance
        self.account = account
        if not account:
            from tests.resources.helper_functions import get_publisher_account
            self.account = get_publisher_account()

    @staticmethod
    def consume_service(service_agreement_id, service_endpoint, account_address, files,
                        destination_folder, *_, **__):
        for f in files:
            with open(os.path.join(destination_folder, os.path.basename(f['url'])), 'w') as of:
                of.write(f'mock data {service_agreement_id}.{service_endpoint}.{account_address}')

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
        return f'{DataServiceProvider.get_url(config)}/services/download'

    @staticmethod
    def get_compute_endpoint(config):
        return f'{DataServiceProvider.get_url(config)}/services/compute'
