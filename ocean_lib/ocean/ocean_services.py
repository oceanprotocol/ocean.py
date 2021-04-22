#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""Ocean module."""
from ocean_lib.common.agreements.service_factory import ServiceDescriptor
from ocean_lib.config_provider import ConfigProvider
from ocean_lib.data_provider.data_service_provider import DataServiceProvider


class OceanServices:

    """Ocean services class."""

    @staticmethod
    def create_access_service(attributes, provider_uri=None):
        """Publish an asset with an `Access` service according to the supplied attributes.

        :param attributes: attributes of the access service, dict
        :param provider_uri: str URL of service provider. This will be used as base to
            construct the serviceEndpoint for the `access` (download) service
        :return: Service instance or None
        """
        service_endpoint = provider_uri or DataServiceProvider.get_url(
            ConfigProvider.get_config()
        )
        service = ServiceDescriptor.access_service_descriptor(
            attributes, service_endpoint
        )
        return service

    @staticmethod
    def create_compute_service(attributes, provider_uri=None):
        service_endpoint = provider_uri or DataServiceProvider.get_url(
            ConfigProvider.get_config()
        )
        return ServiceDescriptor.compute_service_descriptor(
            attributes, service_endpoint
        )
