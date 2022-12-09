#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json
import os
import pathlib
from typing import List

import requests

from ocean_lib.agreements.service_types import ServiceTypes
from ocean_lib.assets.ddo import DDO
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.models.datatoken import Datatoken
from ocean_lib.models.factory_router import FactoryRouter
from ocean_lib.models.fixed_rate_exchange import FixedRateExchange
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.ocean.ocean_assets import DatatokenArguments
from ocean_lib.services.service import Service
from ocean_lib.structures.algorithm_metadata import AlgorithmMetadata
from ocean_lib.structures.file_objects import FilesTypeFactory, UrlFile
from tests.resources.helper_functions import deploy_erc721_erc20, get_file1, get_file2


def get_resource_path(dir_name, file_name):
    base = os.path.realpath(__file__).split(os.path.sep)[1:-1]
    if dir_name:
        return pathlib.Path(os.path.join(os.path.sep, *base, dir_name, file_name))
    else:
        return pathlib.Path(os.path.join(os.path.sep, *base, file_name))


def get_metadata() -> dict:
    path = get_resource_path("ddo", "valid_metadata.json")
    assert path.exists(), f"{path} does not exist!"
    with open(path, "r") as file_handle:
        metadata = file_handle.read()
    return json.loads(metadata)


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


def get_sample_algorithm_ddo_dict(filename="ddo_algorithm.json") -> dict:
    path = get_resource_path("ddo", filename)
    assert path.exists(), f"{path} does not exist!"
    with open(path, "r") as file_handle:
        metadata = file_handle.read()
    return json.loads(metadata)


def get_sample_algorithm_ddo(filename="ddo_algorithm.json") -> DDO:
    return DDO.from_dict(get_sample_algorithm_ddo_dict(filename))


def get_default_metadata(
    asset_type: str = "dataset",
):
    """Helper for asset creation, based on ddo_sa_sample.json

    Optional arguments:
    :param asset_type: used to populate metadata.type, optionally set to "algorithm"
    :param files: list of file objects creates with FilesTypeFactory
    """
    return {
        "created": "2020-11-15T12:27:48Z",
        "updated": "2021-05-17T21:58:02Z",
        "description": "Sample description",
        "name": "Sample asset",
        "type": asset_type,
        "author": "OPF",
        "license": "https://market.oceanprotocol.com/terms",
    }


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


def get_registered_asset_with_access_service(
    ocean_instance, publisher_wallet, metadata=None, more_files=False
):
    url = "https://raw.githubusercontent.com/trentmc/branin/main/branin.arff"
    files = [UrlFile(url)] if not more_files else [UrlFile(url), get_file2()]

    if not metadata:
        metadata = get_default_metadata()

    data_nft, dts, ddo = ocean_instance.assets.create(
        metadata,
        publisher_wallet,
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
        publisher_wallet=publisher_wallet,
        services=[compute_service],
        data_nft_address=data_nft.address,
        deployed_datatokens=[datatoken],
        encrypt_flag=True,
        compress_flag=True,
    )


def get_registered_algorithm_with_access_service(
    ocean_instance: Ocean, publisher_wallet
):
    metadata = get_default_metadata(asset_type="algorithm")

    # Update metadata to include algorithm info
    algorithm_values = {
        "algorithm": {
            "language": "Node.js",
            "format": "docker-image",
            "version": "0.1",
            "container": {
                "entrypoint": "python $ALGO",
                "image": "oceanprotocol/algo_dockers",
                "tag": "python-branin",
                "checksum": "sha256:8221d20c1c16491d7d56b9657ea09082c0ee4a8ab1a6621fa720da58b09580e4",
            },
        }
    }
    metadata.update(algorithm_values)

    algorithm_file = FilesTypeFactory(
        {
            "type": "url",
            "url": "https://raw.githubusercontent.com/oceanprotocol/c2d-examples/main/branin_and_gpr/gpr.py",
            "method": "GET",
        }
    )

    return ocean_instance.assets.create(
        metadata=metadata,
        publisher_wallet=publisher_wallet,
        datatoken_args=[DatatokenArguments("Algo DT1", "DT1", files=[algorithm_file])],
    )


def get_raw_algorithm() -> str:
    req = requests.get(
        "https://raw.githubusercontent.com/oceanprotocol/test-algorithm/master/javascript/algo.js"
    )
    return AlgorithmMetadata(
        {
            "rawcode": req.text,
            "language": "Node.js",
            "format": "docker-image",
            "version": "0.1",
            "container": {
                "entrypoint": "python $ALGO",
                "image": "oceanprotocol/algo_dockers",
                "tag": "python-branin",
                "checksum": "sha256:8221d20c1c16491d7d56b9657ea09082c0ee4a8ab1a6621fa720da58b09580e4",
            },
        }
    )


def build_credentials_dict() -> dict:
    """Build a credentials dict, used for testing."""
    return {"allow": [], "deny": []}


def get_first_service_by_type(ddo, service_type: str) -> Service:
    """Return the first Service with the given service type."""
    return next((service for service in ddo.services if service.type == service_type))
