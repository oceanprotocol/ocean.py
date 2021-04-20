#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_lib.common.agreements.service_types import ServiceTypes
from ocean_lib.common.ddo.ddo import DDO


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
        return self.get_compute_privacy_attributes().get("publisherTrustedAlgorithms")

    def get_compute_privacy_attributes(self):
        service = self.get_service(ServiceTypes.CLOUD_COMPUTE)
        assert service is not None, "this asset does not have a compute service."
        return service.attributes["main"].get("privacy", {})

    def update_compute_privacy(
        self, trusted_algorithms: list, allow_all: bool, allow_raw_algorithm: bool
    ):
        """Set the `trusted_algorithms` on the compute service.

        - An assertion is raised if this asset has no compute service
        - Updates the compute service in place
        - Adds the trusted algorithms under privacy.publisherTrustedAlgorithms
        - If list is empty or trusted_algorithms is None, the `privacy` section is deleted

        :param trusted_algorithms: list of dicts, each dict contain the keys
            ("containerSectionChecksum", "filesChecksum", "did")
        :param allow_all: bool -- set to True to allow all published algorithms to run on this dataset
        :param allow_raw_algorithm: bool -- determine whether raw algorithms (i.e. unpublished) can be run on this dataset
        :return: None
        :raises AssertionError if this asset has no `ServiceTypes.CLOUD_COMPUTE` service
        """
        assert not trusted_algorithms or isinstance(trusted_algorithms, list)
        service = self.get_service(ServiceTypes.CLOUD_COMPUTE)
        assert service is not None, "this asset does not have a compute service."

        trusted_algorithms = trusted_algorithms if trusted_algorithms else []
        if trusted_algorithms:
            for ta in trusted_algorithms:
                assert isinstance(
                    ta, dict
                ), f"item in list of trusted_algorithms must be a dict, got {ta}"
                assert (
                    "did" in ta
                ), f"dict in list of trusted_algorithms is expected to have a `did` key, got {ta.keys()}."

        if not service.attributes["main"].get("privacy"):
            service.attributes["main"]["privacy"] = {}

        service.attributes["main"]["privacy"][
            "publisherTrustedAlgorithms"
        ] = trusted_algorithms
        service.attributes["main"]["privacy"]["allowAllPublishedAlgorithms"] = allow_all
        service.attributes["main"]["privacy"]["allowRawAlgorithm"] = allow_raw_algorithm
