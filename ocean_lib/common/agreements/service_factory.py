#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import Sequence

from enforce_typing import enforce_types
from ocean_lib.common.agreements.service_agreement import ServiceAgreement
from ocean_lib.common.agreements.service_types import ServiceTypes, ServiceTypesIndices
from ocean_lib.common.ddo.service import Service


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
    def authorization_service_descriptor(service_endpoint: str) -> tuple:
        """
        Authorization service descriptor.

        :param service_endpoint: identifier of the service inside the asset DDO, str
        :return: Service descriptor.
        """
        return (
            ServiceTypes.AUTHORIZATION,
            {"attributes": {"main": {}}, "serviceEndpoint": service_endpoint},
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


class ServiceFactory(object):
    """Factory class to create Services."""

    @staticmethod
    @enforce_types
    def build_services(service_descriptors: Sequence) -> list:
        """
        Build a list of services.

        :param service_descriptors: List of tuples of length 2. The first item must be one of
        ServiceTypes
        and the second item is a dict of parameters and values required by the service
        :return: List of Services
        """
        services = []
        for i, service_desc in enumerate(service_descriptors):
            service = ServiceFactory.build_service(service_desc)
            # set index for each service
            service.update_value(ServiceAgreement.SERVICE_INDEX, int(i))
            services.append(service)

        return services

    @staticmethod
    @enforce_types
    def build_service(service_descriptor: Sequence) -> Service:
        """
        Build a service.

        :param service_descriptor: Tuples of length 2. The first item must be one of ServiceTypes
        and the second item is a dict of parameters and values required by the service
        :return: Service
        """
        assert (
            isinstance(service_descriptor, tuple) and len(service_descriptor) == 2
        ), "Unknown service descriptor format."
        service_type, kwargs = service_descriptor
        if service_type == ServiceTypes.METADATA:
            return ServiceFactory.build_metadata_service(
                kwargs["attributes"], kwargs["serviceEndpoint"]
            )

        elif service_type == ServiceTypes.AUTHORIZATION:
            return ServiceFactory.build_authorization_service(
                kwargs["attributes"], kwargs["serviceEndpoint"]
            )

        elif service_type == ServiceTypes.ASSET_ACCESS:
            return ServiceFactory.build_access_service(
                kwargs["attributes"], kwargs["serviceEndpoint"]
            )
        elif service_type == ServiceTypes.CLOUD_COMPUTE:
            return ServiceFactory.build_compute_service(
                kwargs["attributes"], kwargs["serviceEndpoint"]
            )
        raise ValueError(f"Unknown service type {service_type}")

    @staticmethod
    @enforce_types
    def build_metadata_service(metadata: dict, service_endpoint: str) -> Service:
        """
        Build a metadata service.

        :param metadata: conforming to the Metadata accepted by Ocean Protocol, dict
        :param service_endpoint: identifier of the service inside the asset DDO, str
        :return: Service
        """
        return Service(
            service_endpoint,
            ServiceTypes.METADATA,
            attributes=metadata,
            index=ServiceTypesIndices.DEFAULT_METADATA_INDEX,
        )

    @staticmethod
    @enforce_types
    def build_authorization_service(attributes: dict, service_endpoint: str) -> Service:
        """
        Build an authorization service.

        :param attributes: attributes of authorization service, dict
        :param service_endpoint: identifier of the service inside the asset DDO, str
        :return: Service
        """
        return Service(
            service_endpoint,
            ServiceTypes.AUTHORIZATION,
            attributes=attributes,
            index=ServiceTypesIndices.DEFAULT_AUTHORIZATION_INDEX,
        )

    @staticmethod
    @enforce_types
    def build_access_service(
        attributes: dict, service_endpoint: str
    ) -> ServiceAgreement:
        """
        Build an authorization service.

        :param attributes: attributes of access service, dict
        :param service_endpoint: identifier of the service inside the asset DDO, str
        :return: ServiceAgreement instance
        """
        return ServiceAgreement(
            attributes,
            service_endpoint,
            ServiceTypes.ASSET_ACCESS,
            ServiceTypesIndices.DEFAULT_ACCESS_INDEX,
        )

    @staticmethod
    @enforce_types
    def build_compute_service(
        attributes: dict, service_endpoint: str
    ) -> ServiceAgreement:
        """
        Build an authorization service.

        :param attributes: attributes of compute service, dict
        :param service_endpoint: identifier of the service inside the asset DDO, str
        :return: ServiceAgreement instance
        """
        return ServiceAgreement(
            attributes,
            service_endpoint,
            ServiceTypes.CLOUD_COMPUTE,
            ServiceTypesIndices.DEFAULT_COMPUTING_INDEX,
        )
