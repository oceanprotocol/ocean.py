#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
"""
    Service Class for V4
    To handle service items in a DDO record
"""
import copy
import logging
import re
from typing import Any, Dict, List, Optional, Union

from web3.main import Web3

from ocean_lib.agreements.service_types import ServiceTypes, ServiceTypesNames
from ocean_lib.data_provider.data_encryptor import DataEncryptor
from ocean_lib.services.consumer_parameters import ConsumerParameters
from ocean_lib.structures.file_objects import FilesType

logger = logging.getLogger(__name__)


class Service:
    """Service class to create validate service in a V4 DDO."""

    def __init__(
        self,
        service_id: str,
        service_type: str,
        service_endpoint: Optional[str],
        datatoken: Optional[str],
        files: Optional[Union[List[FilesType], str]],
        timeout: Optional[int],
        compute_values: Optional[Dict[str, Any]] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        additional_information: Optional[Dict[str, Any]] = None,
        consumer_parameters=None,
    ) -> None:
        """Initialize NFT Service instance."""
        self.id = service_id
        self.type = service_type
        self.service_endpoint = service_endpoint
        self.datatoken = datatoken
        self.files = files
        self.timeout = timeout
        self.compute_values = compute_values
        self.name = name
        self.description = description
        self.additional_information = None
        self.consumer_parameters = consumer_parameters

        if consumer_parameters:
            try:
                self.consumer_parameters = [
                    ConsumerParameters.from_dict(cp_dict)
                    for cp_dict in consumer_parameters
                ]
            except AttributeError:
                raise TypeError("ConsumerParameters should be a list of dictionaries.")

        if additional_information:
            self.additional_information = additional_information

        if not name or not description:
            service_to_default_name = {
                ServiceTypes.ASSET_ACCESS: ServiceTypesNames.DEFAULT_ACCESS_NAME,
                ServiceTypes.CLOUD_COMPUTE: ServiceTypesNames.DEFAULT_COMPUTE_NAME,
            }

            if service_type in service_to_default_name:
                self.name = service_to_default_name[service_type]
                self.description = service_to_default_name[service_type]

    @classmethod
    def from_dict(cls, service_dict: Dict[str, Any]) -> "Service":
        """Create a service object from a JSON string."""
        sd = copy.deepcopy(service_dict)
        service_type = sd.pop("type", None)

        if not service_type:
            logger.error(
                'Service definition in DDO document is missing the "type" key/value.'
            )
            raise IndexError

        return cls(
            sd.pop("id", None),
            service_type,
            sd.pop("serviceEndpoint", None),
            sd.pop("datatokenAddress", None),
            sd.pop("files", None),
            sd.pop("timeout", None),
            sd.pop("compute", None),
            sd.pop("name", None),
            sd.pop("description", None),
            sd.pop("additionalInformation", None),
            sd.pop("consumerParameters", None),
        )

    def get_trusted_algorithms(self) -> list:
        return self.compute_values.get("publisherTrustedAlgorithms", [])

    def get_trusted_algorithm_publishers(self) -> list:
        return self.compute_values.get("publisherTrustedAlgorithmPublishers", [])

    # Not type provided due to circular imports
    def add_publisher_trusted_algorithm(self, algo_ddo) -> list:
        """
        :return: List of trusted algos
        """
        if self.type != ServiceTypes.CLOUD_COMPUTE:
            raise AssertionError("Service is not compute type")

        initial_trusted_algos_v4 = self.get_trusted_algorithms()

        # remove algo_did if already in the list
        trusted_algos = [
            ta for ta in initial_trusted_algos_v4 if ta["did"] != algo_ddo.did
        ]
        initial_count = len(trusted_algos)

        generated_trusted_algo_dict = algo_ddo.generate_trusted_algorithms()
        trusted_algos.append(generated_trusted_algo_dict)

        # update with the new list
        self.compute_values["publisherTrustedAlgorithms"] = trusted_algos

        assert (
            len(self.compute_values["publisherTrustedAlgorithms"]) > initial_count
        ), "New trusted algorithm was not added. Failed when updating the privacy key. "

        return trusted_algos

    def add_publisher_trusted_algorithm_publisher(self, publisher_address: str) -> list:
        trusted_algo_publishers = [
            Web3.toChecksumAddress(tp) for tp in self.get_trusted_algorithm_publishers()
        ]
        publisher_address = Web3.toChecksumAddress(publisher_address)

        if publisher_address in trusted_algo_publishers:
            return trusted_algo_publishers

        initial_len = len(trusted_algo_publishers)
        trusted_algo_publishers.append(publisher_address)

        # update with the new list
        self.compute_values[
            "publisherTrustedAlgorithmPublishers"
        ] = trusted_algo_publishers
        assert (
            len(self.compute_values["publisherTrustedAlgorithmPublishers"])
            > initial_len
        ), "New trusted algorithm was not added. Failed when updating the privacy key. "

        return trusted_algo_publishers

    def as_dictionary(self) -> Dict[str, Any]:
        """Return the service as a python dictionary."""
        # camelCase to snake case dict, matching the dict value to the attribute name
        key_names = {
            x: re.sub("([A-Z]+)", r"_\1", x).lower()
            for x in [
                "name",
                "description",
                "id",
                "type",
                "files",
                "datatokenAddress",
                "serviceEndpoint",
                "timeout",
                "additionalInformation",
                "consumerParameters",
            ]
        }

        key_names["datatokenAddress"] = "datatoken"

        optional_keys = [
            "name",
            "description",
            "additionalInformation",
            "consumerParameters",
        ]

        values = {}
        if self.type == "compute":
            if "compute" in self.compute_values:
                values.update(self.compute_values)
            else:
                values["compute"] = self.compute_values

        for key, attr_name in key_names.items():
            value = getattr(self, attr_name)

            if isinstance(value, object) and hasattr(value, "as_dictionary"):
                value = value.as_dictionary()
            elif isinstance(value, list):
                value = [
                    v.as_dictionary() if hasattr(v, "as_dictionary") else v
                    for v in value
                ]

            if key in optional_keys and value is None:
                continue

            values[key] = value

        return values

    def remove_publisher_trusted_algorithm(self, algo_did: str) -> list:
        """Returns a trusted algorithms list after removal."""
        trusted_algorithms = self.get_trusted_algorithms()
        if not trusted_algorithms:
            raise ValueError(
                f"Algorithm {algo_did} is not in trusted algorithms of this asset."
            )
        trusted_algorithms = [ta for ta in trusted_algorithms if ta["did"] != algo_did]
        trusted_algo_publishers = self.get_trusted_algorithm_publishers()
        self.update_compute_values(
            trusted_algorithms,
            trusted_algo_publishers,
            allow_network_access=True,
            allow_raw_algorithm=False,
        )
        assert (
            self.compute_values["publisherTrustedAlgorithms"] == trusted_algorithms
        ), "New trusted algorithm was not removed. Failed when updating the list of trusted algorithms. "

        return trusted_algorithms

    def remove_publisher_trusted_algorithm_publisher(
        self, publisher_address: str
    ) -> list:
        """
        :return: List of trusted algo publishers not containing `publisher_address`.
        """
        trusted_algorithm_publishers = [
            tp.lower() for tp in self.get_trusted_algorithm_publishers()
        ]
        publisher_address = publisher_address.lower()
        if not trusted_algorithm_publishers:
            raise ValueError(
                f"Publisher {publisher_address} is not in trusted algorithm publishers of this asset."
            )

        trusted_algorithm_publishers = [
            tp for tp in trusted_algorithm_publishers if tp != publisher_address
        ]
        trusted_algorithms = self.get_trusted_algorithms()
        self.update_compute_values(
            trusted_algorithms, trusted_algorithm_publishers, True, False
        )
        assert (
            self.compute_values["publisherTrustedAlgorithmPublishers"]
            == trusted_algorithm_publishers
        ), "New trusted algorithm publisher was not removed. Failed when updating the list of trusted algo publishers. "

        return trusted_algorithm_publishers

    def update_compute_values(
        self,
        trusted_algorithms: List,
        trusted_algo_publishers: Optional[List],
        allow_network_access: bool,
        allow_raw_algorithm: bool,
    ) -> None:
        """Set the `trusted_algorithms` on the compute service.

        - An assertion is raised if this asset has no compute service
        - Updates the compute service in place
        - Adds the trusted algorithms under privacy.publisherTrustedAlgorithms

        :param trusted_algorithms: list of dicts, each dict contain the keys
            ("containerSectionChecksum", "filesChecksum", "did")
        :param trusted_algo_publishers: list of strings, addresses of trusted publishers
        :param allow_network_access: bool -- set to True to allow network access to all the algorithms that belong to this dataset
        :param allow_raw_algorithm: bool -- determine whether raw algorithms (i.e. unpublished) can be run on this dataset
        :return: None
        :raises AssertionError if this asset has no `ServiceTypes.CLOUD_COMPUTE` service
        """
        assert not trusted_algorithms or isinstance(trusted_algorithms, list)
        assert (
            self.type == ServiceTypes.CLOUD_COMPUTE is not None
        ), "this asset does not have a compute service."

        for ta in trusted_algorithms:
            assert isinstance(
                ta, dict
            ), f"item in list of trusted_algorithms must be a dict, got {ta}"
            assert (
                "did" in ta
            ), f"dict in list of trusted_algorithms is expected to have a `did` key, got {ta.keys()}."

        if not self.compute_values:
            self.compute_values = {}

        self.compute_values["publisherTrustedAlgorithms"] = trusted_algorithms
        self.compute_values[
            "publisherTrustedAlgorithmPublishers"
        ] = trusted_algo_publishers
        self.compute_values["allowNetworkAccess"] = allow_network_access
        self.compute_values["allowRawAlgorithm"] = allow_raw_algorithm

    def encrypt_files(self, nft_address):
        if self.files and isinstance(self.files, str):
            return

        files = list(map(lambda file: file.to_dict(), self.files))

        encrypt_response = DataEncryptor.encrypt(
            {
                "datatokenAddress": self.datatoken,
                "nftAddress": nft_address,
                "files": files,
            },
            self.service_endpoint,
        )

        self.files = encrypt_response.content.decode("utf-8")
