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

    def get_trusted_algorithms(self):
        service = self.get_service(ServiceTypes.CLOUD_COMPUTE)
        assert service is not None, "this asset does not have a compute service."
        privacy_values = service.attributes["main"].get("privacy", {})
        return privacy_values.get("publisherTrustedAlgorithms")

    def update_trusted_algorithms(self, trusted_algorithms: list):
        """Set the `trusted_algorithms` on the compute service.

        - An assertion is raised if this asset has no compute service
        - Updates the compute service in place
        - Adds the trusted algorithms under privacy.publisherTrustedAlgorithms
        - If list is empty or trusted_algorithms is None, the `privacy` section is deleted

        :param trusted_algorithms: list of dicts, each dict contain the keys
            ("containerSectionChecksum", "filesChecksum", "did")
        :return: None
        """
        assert not trusted_algorithms or isinstance(trusted_algorithms, list)
        service = self.get_service(ServiceTypes.CLOUD_COMPUTE)
        assert service is not None, "this asset does not have a compute service."

        if not trusted_algorithms:
            service.attributes["main"].pop("privacy", None)
            return

        keys = {"containerSectionChecksum", "filesChecksum", "did"}
        for ta in trusted_algorithms:
            assert isinstance(
                ta, dict
            ), f"item in list of trusted_algorithms must be a dict, got {ta}"
            assert keys == set(
                ta.keys()
            ), f"dict in list of trusted_algorithms is expected to have the keys {keys}, got {ta.keys()}."

        service.attributes["main"]["privacy"] = {
            "publisherTrustedAlgorithms": trusted_algorithms
        }
