#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json
import os
import pathlib
import time
import uuid

from ocean_lib.assets.asset import Asset
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.models.algorithm_metadata import AlgorithmMetadata
from ocean_lib.web3_internal.wallet import Wallet
from ocean_utils.agreements.service_factory import ServiceDescriptor
from ocean_utils.agreements.service_types import ServiceTypes
from ocean_utils.ddo.metadata import MetadataMain
from tests.resources.helper_functions import mint_tokens_and_wait


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


def get_sample_ddo() -> Asset:
    return Asset(json_filename=get_resource_path("ddo", "ddo_sa_sample.json"))


def get_sample_ddo_with_compute_service() -> Asset:
    return Asset(
        json_filename=get_resource_path("ddo", "ddo_with_compute_service.json")
    )


def get_sample_algorithm_ddo() -> dict:
    path = get_resource_path("ddo", "ddo_algorithm.json")
    assert path.exists(), f"{path} does not exist!"
    with open(path, "r") as file_handle:
        metadata = file_handle.read()
    return json.loads(metadata)


def get_algorithm_meta():
    algorithm_ddo_path = get_resource_path("ddo", "ddo_algorithm.json")
    algo_main = Asset(json_filename=algorithm_ddo_path).metadata["main"]
    algo_meta_dict = algo_main["algorithm"].copy()
    algo_meta_dict["url"] = algo_main["files"][0]["url"]
    return AlgorithmMetadata(algo_meta_dict)


def get_access_service_descriptor(
    ocean_instance, address, date_created, provider_uri=None, timeout=3600
):
    if not provider_uri:
        provider_uri = DataServiceProvider.get_url(ocean_instance.config)

    return ServiceDescriptor.access_service_descriptor(
        ocean_instance.assets.build_access_service(date_created, 1.0, address, timeout),
        DataServiceProvider.build_download_endpoint(provider_uri)[1],
    )


def get_computing_metadata() -> dict:
    path = get_resource_path("ddo", "computing_metadata.json")
    assert path.exists(), f"{path} does not exist!"
    with open(path, "r") as file_handle:
        metadata = file_handle.read()
    return json.loads(metadata)


def get_registered_ddo(
    ocean_instance,
    metadata,
    wallet: Wallet,
    service_descriptor=None,
    datatoken=None,
    provider_uri=None,
):
    metadata["main"]["files"][0]["checksum"] = str(uuid.uuid4())
    if not service_descriptor:
        service_descriptor = get_access_service_descriptor(
            ocean_instance,
            wallet.address,
            metadata[MetadataMain.KEY]["dateCreated"],
            provider_uri,
        )

    block = ocean_instance.web3.eth.blockNumber
    asset = ocean_instance.assets.create(
        metadata,
        wallet,
        service_descriptors=[service_descriptor],
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
    service_descriptor = get_access_service_descriptor(
        ocean_instance,
        wallet.address,
        metadata[MetadataMain.KEY]["dateCreated"],
        provider_uri,
    )

    return get_registered_ddo(
        ocean_instance, metadata, wallet, service_descriptor, provider_uri=provider_uri
    )


def get_registered_ddo_with_compute_service(
    ocean_instance, wallet, provider_uri=None, trusted_algorithms=None
):
    old_ddo = get_sample_ddo_with_compute_service()
    metadata = old_ddo.metadata
    metadata["main"]["files"][0]["checksum"] = str(uuid.uuid4())
    service = old_ddo.get_service(ServiceTypes.CLOUD_COMPUTE)
    compute_attributes = ocean_instance.compute.create_compute_service_attributes(
        service.attributes["main"]["timeout"],
        service.attributes["main"]["creator"],
        service.attributes["main"]["datePublished"],
        service.attributes["main"]["provider"],
        privacy_attributes=ocean_instance.compute.build_service_privacy_attributes(
            trusted_algorithms,
            allow_raw_algorithm=True,
            allow_all_published_algorithms=not bool(trusted_algorithms),
        ),
    )
    compute_service = ServiceDescriptor.compute_service_descriptor(
        compute_attributes, DataServiceProvider.get_url(ocean_instance.config)
    )

    return get_registered_ddo(
        ocean_instance, metadata, wallet, compute_service, provider_uri=provider_uri
    )


def get_registered_algorithm_ddo(ocean_instance, wallet, provider_uri=None):
    metadata = get_sample_algorithm_ddo()["service"][0]["attributes"]
    metadata["main"]["files"][0]["checksum"] = str(uuid.uuid4())
    service_descriptor = get_access_service_descriptor(
        ocean_instance,
        wallet.address,
        metadata[MetadataMain.KEY]["dateCreated"],
        provider_uri,
    )
    if "cost" in metadata[MetadataMain.KEY]:
        metadata[MetadataMain.KEY].pop("cost")
    return get_registered_ddo(
        ocean_instance, metadata, wallet, service_descriptor, provider_uri=provider_uri
    )


def get_registered_algorithm_ddo_different_provider(ocean_instance, wallet):
    return get_registered_algorithm_ddo(
        ocean_instance, wallet, "http://172.15.0.7:8030"
    )


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
