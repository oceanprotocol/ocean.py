#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json
import os
import pathlib
import time
import uuid

from ocean_lib.agreements.service_types import ServiceTypes
from ocean_lib.assets.asset import Asset
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.ocean import Ocean
from ocean_lib.ocean.test.test_ocean_assets import create_basics
from ocean_lib.services.service import Service
from ocean_lib.web3_internal.wallet import Wallet
from tests.resources.helper_functions import deploy_erc721_erc20, mint_tokens_and_wait


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


def get_registered_ddo(
    ocean_instance,
    metadata,
    wallet: Wallet,
    service=None,
    datatoken=None,
    provider_uri=None,
):
    metadata["main"]["files"][0]["checksum"] = str(uuid.uuid4())

    if not service:
        service = get_access_service(
            ocean_instance,
            wallet.address,
            metadata["main"]["dateCreated"],
            provider_uri,
        )

    block = ocean_instance.web3.eth.block_number
    asset = ocean_instance.assets.create(
        metadata,
        wallet,
        services=[service],
        data_token_address=datatoken,
        provider_uri=provider_uri,
    )
    ddo_reg = ocean_instance.assets.ddo_registry()
    log = ddo_reg.get_event_log(
        ddo_reg.EVENT_METADATA_CREATED, block, asset.asset_id, 30
    )
    assert log, "no ddo created event."

    # Mint tokens for dataset and assign to publisher
    dt = ocean_instance.get_data_token(asset.data_token_address)
    mint_tokens_and_wait(dt, wallet.address, wallet)

    ddo = wait_for_ddo(ocean_instance, asset.did)
    assert ddo, f"resolve did {asset.did} failed."

    return asset


def get_registered_ddo_with_access_service(ocean_instance, wallet, provider_uri=None):
    old_ddo = get_sample_ddo_with_compute_service()
    metadata = old_ddo.metadata
    metadata["main"]["files"][0]["checksum"] = str(uuid.uuid4())
    service = get_access_service(
        ocean_instance, wallet.address, metadata["main"]["dateCreated"], provider_uri
    )

    return get_registered_ddo(
        ocean_instance, metadata, wallet, service, provider_uri=provider_uri
    )


def get_registered_ddo_with_compute_service(
    ocean_instance: Ocean, publisher_wallet: Wallet
):
    erc721_token, erc20_token = deploy_erc721_erc20(
        ocean_instance.web3, ocean_instance.config, publisher_wallet
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
        "allowRawAlgorithm": False,
        "allowNetworkAccess": True,
    }
    compute_service = Service(
        service_id="2",
        service_type=ServiceTypes.CLOUD_COMPUTE,
        service_endpoint=f"{data_provider.get_url(config)}/api/services/compute",
        data_token=erc20_token.address,
        files=encrypted_files,
        timeout=3600,
        compute_values=compute_values,
    )

    return ocean_instance.assets.create(
        metadata=metadata,
        publisher_wallet=publisher_wallet,
        encrypted_files=encrypted_files,
        services=[compute_service],
        erc721_address=erc721_token.address,
        deployed_erc20_tokens=[erc20_token],
        encrypt_flag=True,
        compress_flag=True,
    )


def get_registered_algorithm_ddo(ocean_instance: Ocean, publisher_wallet: Wallet):
    erc721_token, erc20_token = deploy_erc721_erc20(
        ocean_instance.web3, ocean_instance.config, publisher_wallet
    )

    web3 = ocean_instance.web3
    config = ocean_instance.config
    data_provider = DataServiceProvider
    _, metadata, encrypted_files = create_basics(config, web3, data_provider)

    # Update metadata to include algorithm info
    algorithm_values = {
        "algorithm": {
            "language": "scala",
            "format": "docker-image",
            "version": "0.1",
            "container": {
                "entrypoint": "node $ALGO",
                "image": "node",
                "tag": "10",
                "checksum": "test",
            },
        }
    }
    metadata.update(algorithm_values)

    access_service = Service(
        service_id="1",
        service_type=ServiceTypes.ASSET_ACCESS,
        service_endpoint=f"{data_provider.get_url(config)}/api/services/download",
        data_token=erc20_token.address,
        files=encrypted_files,
        timeout=0,
    )

    return ocean_instance.assets.create(
        metadata=metadata,
        publisher_wallet=publisher_wallet,
        encrypted_files=encrypted_files,
        services=[access_service],
        erc721_address=erc721_token.address,
        deployed_erc20_tokens=[erc20_token],
        encrypt_flag=True,
        compress_flag=True,
    )


def get_registered_algorithm_ddo_different_provider(ocean_instance, wallet):
    return get_registered_algorithm_ddo(
        ocean_instance, wallet, "http://172.15.0.7:8030"
    )


def build_credentials_dict() -> dict:
    """Build a credentials dict, used for testing."""
    return {"allow": [], "deny": []}


def wait_for_update(ocean, did, updated_attr, value, timeout=30):
    start = time.time()
    ddo = None
    while True:
        try:
            ddo = ocean.assets.resolve(did)
        except ValueError:
            pass

        if not ddo:
            time.sleep(0.2)
        elif ddo.metadata["main"].get(updated_attr) == value:
            break

        if time.time() - start > timeout:
            break

    return ddo


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
