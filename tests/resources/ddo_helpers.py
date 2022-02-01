#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json
import os
import pathlib
import time
from typing import List, Optional, Union

import requests

from ocean_lib.agreements.file_objects import FilesTypeFactory, IpfsFile, UrlFile
from ocean_lib.agreements.service_types import ServiceTypes
from ocean_lib.assets.asset import Asset
from ocean_lib.assets.trusted_algorithms import generate_trusted_algo_dict
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.models.algorithm_metadata import AlgorithmMetadata
from ocean_lib.models.erc721_factory import ERC721FactoryContract
from ocean_lib.models.models_structures import CreateErc20Data
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.ocean.util import get_address_of_type
from ocean_lib.services.service import Service
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.currency import to_wei
from ocean_lib.web3_internal.wallet import Wallet
from tests.resources.helper_functions import deploy_erc721_erc20


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


def get_sample_algorithm_ddo(filename="ddo_algorithm.json") -> Asset:
    return Asset.from_dict(get_sample_algorithm_ddo_dict(filename))


def get_access_service(
    ocean_instance, address, date_created, provider_uri=None, timeout=3600
):
    if not provider_uri:
        provider_uri = DataServiceProvider.get_url(ocean_instance.config)

    return ocean_instance.assets.build_access_service(
        DataServiceProvider.build_download_endpoint(provider_uri)[1],
        date_created,
        1.0,
        address,
        timeout,
    )


def create_asset(ocean, publisher, config, metadata=None, files=None):
    """Helper function for asset creation based on ddo_sa_sample.json."""
    erc20_data = CreateErc20Data(
        template_index=1,
        strings=["Datatoken 1", "DT1"],
        addresses=[
            publisher.address,
            publisher.address,
            ZERO_ADDRESS,
            get_address_of_type(config, "Ocean"),
        ],
        uints=[to_wei(100), 0],
        bytess=[b""],
    )

    if not metadata:
        metadata = {
            "created": "2020-11-15T12:27:48Z",
            "updated": "2021-05-17T21:58:02Z",
            "description": "Sample description",
            "name": "Sample asset",
            "type": "dataset",
            "author": "OPF",
            "license": "https://market.oceanprotocol.com/terms",
        }

    if not files:
        file1_dict = {
            "type": "url",
            "url": "https://url.com/file1.csv",
            "method": "GET",
        }
        file1 = FilesTypeFactory(file1_dict)
        files = [file1]

    # Encrypt file(s) using provider
    encrypted_files = ocean.assets.encrypt_files(files)

    # Publish asset with services on-chain.
    # The download (access service) is automatically created
    asset = ocean.assets.create(
        metadata, publisher, encrypted_files, erc20_tokens_data=[erc20_data]
    )

    return asset


def create_basics(
    config,
    web3,
    data_provider,
    asset_type: str = "dataset",
    files: Optional[List[Union[UrlFile, IpfsFile]]] = None,
):
    """Helper for asset creation, based on ddo_sa_sample.json

    Optional arguments:
    :param asset_type: used to populate metadata.type, optionally set to "algorithm"
    :param files: list of file objects creates with FilesTypeFactory
    """
    erc721_factory_address = get_address_of_type(
        config, ERC721FactoryContract.CONTRACT_NAME
    )
    erc721_factory = ERC721FactoryContract(web3, erc721_factory_address)

    metadata = {
        "created": "2020-11-15T12:27:48Z",
        "updated": "2021-05-17T21:58:02Z",
        "description": "Sample description",
        "name": "Sample asset",
        "type": asset_type,
        "author": "OPF",
        "license": "https://market.oceanprotocol.com/terms",
    }

    if files is None:
        file1_dict = {
            "type": "url",
            "url": "https://url.com/file1.csv",
            "method": "GET",
        }
        file2_dict = {
            "type": "url",
            "url": "https://url.com/file2.csv",
            "method": "GET",
        }
        file1 = FilesTypeFactory(file1_dict)
        file2 = FilesTypeFactory(file2_dict)
        files = [file1, file2]

    # Encrypt file objects
    encrypt_response = data_provider.encrypt(files, config.provider_url)
    encrypted_files = encrypt_response.content.decode("utf-8")

    return erc721_factory, metadata, encrypted_files


def get_registered_asset_with_access_service(ocean_instance, publisher_wallet):
    return create_asset(ocean_instance, publisher_wallet, ocean_instance.config)


def get_registered_asset_with_compute_service(
    ocean_instance: Ocean,
    publisher_wallet: Wallet,
    allow_raw_algorithms: bool = False,
    trusted_algorithms: List[Asset] = [],
    trusted_algorithm_publishers: List[str] = [],
):
    erc721_token, erc20_token = deploy_erc721_erc20(
        ocean_instance.web3, ocean_instance.config, publisher_wallet, publisher_wallet
    )

    web3 = ocean_instance.web3
    config = ocean_instance.config
    data_provider = DataServiceProvider
    _, metadata, encrypted_files = create_basics(config, web3, data_provider)

    # Set the compute values for compute service
    compute_values = {
        "namespace": "ocean-compute",
        "cpus": 2,
        "gpus": 4,
        "gpuType": "NVIDIA Tesla V100 GPU",
        "memory": "128M",
        "volumeSize": "2G",
        "allowRawAlgorithm": allow_raw_algorithms,
        "allowNetworkAccess": True,
    }
    compute_service = Service(
        service_id="2",
        service_type=ServiceTypes.CLOUD_COMPUTE,
        service_endpoint=f"{data_provider.get_url(config)}/api/services/compute",
        datatoken=erc20_token.address,
        files=encrypted_files,
        timeout=3600,
        compute_values=compute_values,
    )

    for algorithm in trusted_algorithms:
        compute_service.add_publisher_trusted_algorithm(
            algorithm, generate_trusted_algo_dict(algorithm)
        )

    for publisher in trusted_algorithm_publishers:
        compute_service.add_publisher_trusted_algorithm_publisher(publisher)

    return ocean_instance.assets.create(
        metadata=metadata,
        publisher_wallet=publisher_wallet,
        services=[compute_service],
        erc721_address=erc721_token.address,
        deployed_erc20_tokens=[erc20_token],
        encrypt_flag=True,
        compress_flag=True,
    )


def get_registered_algorithm_with_access_service(
    ocean_instance: Ocean, publisher_wallet: Wallet
):
    web3 = ocean_instance.web3
    config = ocean_instance.config
    data_provider = DataServiceProvider
    _, metadata, _ = create_basics(config, web3, data_provider, asset_type="algorithm")

    # Update metadata to include algorithm info
    algorithm_values = {
        "algorithm": {
            "language": "Node.js",
            "format": "docker-image",
            "version": "0.1",
            "container": {
                "entrypoint": "node $ALGO",
                "image": "ubuntu",
                "tag": "latest",
                "checksum": "44e10daa6637893f4276bb8d7301eb35306ece50f61ca34dcab550",
            },
        }
    }
    metadata.update(algorithm_values)

    algorithm_file = FilesTypeFactory(
        {
            "type": "url",
            "url": "https://raw.githubusercontent.com/oceanprotocol/test-algorithm/master/javascript/algo.js",
            "method": "GET",
        }
    )

    return create_asset(
        ocean_instance,
        publisher_wallet,
        ocean_instance.config,
        metadata=metadata,
        files=[algorithm_file],
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
                "entrypoint": "node $ALGO",
                "image": "ubuntu",
                "tag": "latest",
                "checksum": "44e10daa6637893f4276bb8d7301eb35306ece50f61ca34dcab550",
            },
        }
    )


def get_registered_algorithm_ddo_different_provider(ocean_instance, wallet):
    return get_registered_algorithm_with_access_service(
        ocean_instance, wallet, "http://172.15.0.7:8030"
    )


def build_credentials_dict() -> dict:
    """Build a credentials dict, used for testing."""
    return {"allow": [], "deny": []}


def wait_for_ddo(ocean, did, timeout=30):
    start = time.time()
    ddo = None
    while not ddo:
        try:
            ddo = ocean.assets.resolve(did)
        except ValueError:
            pass

        if not ddo:
            time.sleep(0.2)

        if time.time() - start > timeout:
            break

    return ddo
