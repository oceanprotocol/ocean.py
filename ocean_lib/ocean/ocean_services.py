#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
"""Ocean module."""
#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0
from ocean_lib.config_provider import ConfigProvider
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_utils.agreements.service_factory import ServiceDescriptor

from ocean_lib.assets.utils import create_publisher_trusted_algorithms


class OceanServices:
    """Ocean services class."""

    @staticmethod
    def create_access_service(attributes, provider_uri=None):
        """
        Publish an asset with an `Access` service according to the supplied attributes.

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

    @staticmethod
    def create_compute_service_attributes(
        timeout: int,
        creator: str,
        date_published: str,
        provider_attributes: dict,
        trusted_algorithms: list = None,
        allow_raw_algorithm: bool = False,
        allow_all_published_algorithms: bool = False,
    ):
        """

        :param timeout: integer maximum amount of running compute service in seconds
        :param creator: str ethereum address
        :param date_published: str timestamp (datetime.utcnow().replace(microsecond=0).isoformat() + "Z")
        :param provider_attributes: dict describing the details of the compute resources (see `build_service_provider_attributes`)
        :param trusted_algorithms: list of algorithm did to be trusted by the compute service provider
        :param allow_raw_algorithm: bool -- when True, unpublished raw algorithm code can be run on this dataset
        :param allow_all_published_algorithms: bool -- when True, any published algorithm can be run on this dataset
            The list of `trusted_algorithms` will be ignored in this case.
        :return: dict with `main` key and value contain the minimum required attributes of a compute service
        """
        attributes = {
            "main": {
                "name": "dataAssetComputingServiceAgreement",
                "creator": creator,
                "datePublished": date_published,
                "cost": 1.0,
                "timeout": timeout,
                "provider": provider_attributes,
                "privacy": {
                    "allowRawAlgorithm": allow_raw_algorithm,
                    "allowAllPublishedAlgorithms": allow_all_published_algorithms,
                    "publisherTrustedAlgorithms": [],
                },
            }
        }
        if trusted_algorithms:
            trusted_algorithms_list = create_publisher_trusted_algorithms(
                trusted_algorithms, ConfigProvider.get_config().aquarius_url
            )
            attributes["main"]["privacy"] = {
                "publisherTrustedAlgorithms": trusted_algorithms_list
            }

        return attributes
