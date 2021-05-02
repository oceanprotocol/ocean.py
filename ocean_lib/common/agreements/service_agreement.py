#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from collections import namedtuple

from ocean_lib.common.agreements.service_types import ServiceTypes, ServiceTypesIndices
from ocean_lib.common.ddo.service import Service

Agreement = namedtuple("Agreement", ("template", "conditions"))


class ServiceAgreement(Service):
    """Class representing a Service Agreement."""

    AGREEMENT_TEMPLATE = "serviceAgreementTemplate"
    SERVICE_CONDITIONS = "conditions"

    def __init__(
        self,
        attributes,
        service_endpoint=None,
        service_type=None,
        service_index=None,
        other_values=None,
    ):
        """

        :param attributes: dict of main attributes of the service. This should
            include `main` and optionally the `additionalInformation` section
        :param service_endpoint: str URL to use for requesting service defined in this agreement
        :param service_type: str like ServiceTypes.ASSET_ACCESS
        :param other_values: dict of other key/value that maybe added and will be kept as is.
        """
        self._other_values = other_values or {}

        service_to_default_index = {
            ServiceTypes.ASSET_ACCESS: ServiceTypesIndices.DEFAULT_ACCESS_INDEX,
            ServiceTypes.CLOUD_COMPUTE: ServiceTypesIndices.DEFAULT_COMPUTING_INDEX,
        }

        if service_type not in service_to_default_index:
            raise ValueError(
                f"The service_type {service_type} is not currently supported. Supported "
                f"service types are {ServiceTypes.ASSET_ACCESS} and {ServiceTypes.CLOUD_COMPUTE}"
            )

        default_index = service_to_default_index[service_type]

        service_index = service_index if service_index is not None else default_index
        Service.__init__(
            self,
            service_endpoint,
            service_type,
            attributes,
            other_values,
            service_index,
        )

    @classmethod
    def from_json(cls, service_dict):
        """

        :param service_dict:
        :return:
        """
        service_endpoint, _type, _index, _attributes, service_dict = cls._parse_json(
            service_dict
        )

        return cls(_attributes, service_endpoint, _type, _index, service_dict)

    @classmethod
    def from_ddo(cls, service_type, ddo):
        """

        :param service_type: identifier of the service inside the asset DDO, str
        :param ddo:
        :return:
        """
        service = ddo.get_service(service_type)
        if not service:
            raise ValueError(
                f"Service of type {service_type} is not found in this DDO."
            )

        service_dict = service.as_dictionary()

        return cls.from_json(service_dict)

    def as_dictionary(self):
        values = Service.as_dictionary(self)
        return values

    def get_cost(self):
        """
        Return the price from the conditions parameters.

        :return: Float
        """
        return float(self.main["cost"])

    @property
    def service_endpoint(self):
        return self._service_endpoint
