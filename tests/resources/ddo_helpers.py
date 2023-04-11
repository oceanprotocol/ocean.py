#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json
import os
import pathlib
from typing import List

from ocean_lib.agreements.service_types import ServiceTypes
from ocean_lib.assets.ddo import DDO
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.models.datatoken_base import DatatokenArguments
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.services.service import Service
from ocean_lib.structures.file_objects import UrlFile
from tests.resources.helper_functions import deploy_erc721_erc20, get_file1, get_file2


def get_resource_path(dir_name, file_name):
    base = os.path.realpath(__file__).split(os.path.sep)[1:-1]
    if dir_name:
        return pathlib.Path(os.path.join(os.path.sep, *base, dir_name, file_name))
    else:
        return pathlib.Path(os.path.join(os.path.sep, *base, file_name))


def get_key_from_v4_sample_ddo(key, file_name="ddo_v4_sample.json"):
    path = get_resource_path("ddo", file_name)
    with open(path, "r") as file_handle:
        ddo = file_handle.read()
    ddo_dict = json.loads(ddo)
    return ddo_dict.pop(key, None)


def get_sample_ddo(file_name="ddo_v4_sample.json") -> dict:
    path = get_resource_path("ddo", file_name)
    with open(path, "r") as file_handle:
        ddo = file_handle.read()
    return json.loads(ddo)


def get_sample_ddo_with_compute_service(
    filename="ddo_v4_with_compute_service.json",
) -> dict:
    path = get_resource_path("ddo", filename)
    with open(path, "r") as file_handle:
        ddo = file_handle.read()
    return json.loads(ddo)


def get_sample_algorithm_ddo(filename="ddo_algorithm.json") -> DDO:
    path = get_resource_path("ddo", filename)
    assert path.exists(), f"{path} does not exist!"

    with open(path, "r") as file_handle:
        metadata = file_handle.read()
    alg_dict = json.loads(metadata)

    return DDO.from_dict(alg_dict)


def get_default_metadata():
    return get_key_from_v4_sample_ddo("metadata")


def get_default_files():
    return [get_file1(), get_file2()]


def build_default_services(config, datatoken):
    files = get_default_files()
    services = [
        datatoken.build_access_service(
            service_id="0",
            service_endpoint=config.get("PROVIDER_URL"),
            files=files,
        )
    ]

    return services


def build_credentials_dict() -> dict:
    """Build a credentials dict, used for testing."""
    return {"allow": [], "deny": []}


def get_registered_asset_with_access_service(
    ocean_instance, publisher_wallet, metadata=None, more_files=False
):
    url = "https://raw.githubusercontent.com/trentmc/branin/main/branin.arff"
    files = [UrlFile(url)] if not more_files else [UrlFile(url), get_file2()]

    if not metadata:
        metadata = get_default_metadata()

    data_nft, dts, ddo = ocean_instance.assets.create(
        metadata,
        {"from": publisher_wallet},
        datatoken_args=[DatatokenArguments("Branin: DT1", "DT1", files=files)],
    )

    return data_nft, dts[0], ddo


def get_registered_asset_with_compute_service(
    ocean_instance: Ocean,
    publisher_wallet,
    allow_raw_algorithms: bool = False,
    trusted_algorithms: List[DDO] = [],
    trusted_algorithm_publishers: List[str] = [],
):
    data_nft, datatoken = deploy_erc721_erc20(
        ocean_instance.config_dict,
        publisher_wallet,
        publisher_wallet,
    )

    config = ocean_instance.config_dict
    data_provider = DataServiceProvider

    arff_file = UrlFile(
        url="https://raw.githubusercontent.com/oceanprotocol/c2d-examples/main/branin_and_gpr/branin.arff"
    )

    metadata = get_default_metadata()
    files = [arff_file]

    # Set the compute values for compute service
    compute_values = {
        "allowRawAlgorithm": allow_raw_algorithms,
        "allowNetworkAccess": True,
        "publisherTrustedAlgorithms": [],
        "publisherTrustedAlgorithmPublishers": [],
    }
    compute_service = Service(
        service_id="2",
        service_type=ServiceTypes.CLOUD_COMPUTE,
        service_endpoint=data_provider.get_url(config),
        datatoken=datatoken.address,
        files=files,
        timeout=3600,
        compute_values=compute_values,
    )

    for algorithm in trusted_algorithms:
        compute_service.add_publisher_trusted_algorithm(algorithm)

    for publisher in trusted_algorithm_publishers:
        compute_service.add_publisher_trusted_algorithm_publisher(publisher)

    return ocean_instance.assets.create(
        metadata=metadata,
        tx_dict={"from": publisher_wallet},
        services=[compute_service],
        data_nft_address=data_nft.address,
        deployed_datatokens=[datatoken],
        encrypt_flag=True,
        compress_flag=True,
    )


def get_first_service_by_type(ddo, service_type: str) -> Service:
    """Return the first Service with the given service type."""
    return next((service for service in ddo.services if service.type == service_type))
