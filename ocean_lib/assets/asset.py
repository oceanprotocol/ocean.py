#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_utils.agreements.service_types import ServiceTypes
from ocean_utils.ddo.ddo import DDO


class Asset(DDO):
    @property
    def data_token_address(self):
        return self._other_values["dataToken"]

    @data_token_address.setter
    def data_token_address(self, token_address):
        self._other_values["dataToken"] = token_address

    @property
    def values(self):
        return self._other_values.copy()

    def update_trusted_algorithms(self, trusted_algorithms: list):
        assert isinstance(trusted_algorithms, list)
        service = self.get_service(ServiceTypes.CLOUD_COMPUTE)
        assert service is not None, "this asset does not have a compute service."
        service.attributes["main"]["privacy"] = {
            "publisherTrustedAlgorithms": trusted_algorithms
        }
