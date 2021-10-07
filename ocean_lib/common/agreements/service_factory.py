#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enforce_typing import enforce_types
from ocean_lib.common.agreements.service_types import ServiceTypes


class ServiceDescriptor(object):
    """Tuples of length 2. The first item must be one of ServiceTypes and the second
    item is a dict of parameters and values required by the service"""

    @staticmethod
    @enforce_types
    def metadata_service_descriptor(attributes: dict, service_endpoint: str) -> tuple:
        """
        Metadata service descriptor.

        :param attributes: conforming to the Metadata accepted by Ocean Protocol, dict
        :param service_endpoint: identifier of the service inside the asset DDO, str
        :return: Service descriptor.
        """
        return (
            ServiceTypes.METADATA,
            {"attributes": attributes, "serviceEndpoint": service_endpoint},
        )

    @staticmethod
    @enforce_types
    def access_service_descriptor(attributes: dict, service_endpoint: str) -> tuple:
        """
        Access service descriptor.

        :param attributes: attributes of the access service, dict
        :param service_endpoint: identifier of the service inside the asset DDO, str
        :param template_id:
        :return: Service descriptor.
        """
        return (
            ServiceTypes.ASSET_ACCESS,
            {"attributes": attributes, "serviceEndpoint": service_endpoint},
        )

    @staticmethod
    @enforce_types
    def compute_service_descriptor(attributes: dict, service_endpoint: str) -> tuple:
        """
        Compute service descriptor.

        :param attributes: attributes of the compute service, dict
        :param service_endpoint: identifier of the service inside the asset DDO, str
        :param template_id:
        :return: Service descriptor.
        """
        return (
            ServiceTypes.CLOUD_COMPUTE,
            {"attributes": attributes, "serviceEndpoint": service_endpoint},
        )
