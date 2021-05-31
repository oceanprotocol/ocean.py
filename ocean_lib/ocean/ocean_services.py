#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""Ocean module."""
from ocean_lib.common.agreements.service_factory import ServiceDescriptor


class OceanServices:

    """Ocean services class."""

    @staticmethod
    def create_access_service(attributes, provider_uri):
        """Publish an asset with an `Access` service according to the supplied attributes.

        :param attributes: attributes of the access service, dict
        :param provider_uri: str URL of service provider. This will be used as base to
            construct the serviceEndpoint for the `access` (download) service
        :return: Service instance or None
        """
        service_endpoint = provider_uri
        service = ServiceDescriptor.access_service_descriptor(
            attributes, service_endpoint
        )
        return service

    @staticmethod
    def create_compute_service(attributes, provider_uri):
        service_endpoint = provider_uri
        return ServiceDescriptor.compute_service_descriptor(
            attributes, service_endpoint
        )
