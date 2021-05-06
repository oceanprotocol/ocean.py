#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import hashlib
import json

from typing import Optional

from ocean_lib.assets.asset import Asset
from ocean_lib.assets.asset_resolver import resolve_asset
from ocean_lib.common.agreements.service_types import ServiceTypes
from ocean_lib.enforce_typing_shim import enforce_types_shim


def create_checksum(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@enforce_types_shim
def generate_trusted_algo_dict(
    did: Optional[str] = None,
    metadata_cache_uri: Optional[str] = None,
    ddo: Optional[Asset] = None,
):
    assert ddo or (
        did and metadata_cache_uri
    ), "Either DDO, or both did and metadata_cache_uri are None."
    if not ddo:
        ddo = resolve_asset(did, metadata_cache_uri=metadata_cache_uri)

    algo_metadata = ddo.metadata
    return {
        "did": ddo.did,
        "filesChecksum": create_checksum(
            algo_metadata["encryptedFiles"]
            + json.dumps(algo_metadata["main"]["files"], separators=(",", ":"))
        ),
        "containerSectionChecksum": create_checksum(
            json.dumps(
                algo_metadata["main"]["algorithm"]["container"], separators=(",", ":")
            )
        ),
    }


@enforce_types_shim
def create_publisher_trusted_algorithms(dids: list, metadata_cache_uri: str) -> list:
    return [
        generate_trusted_algo_dict(did=did, metadata_cache_uri=metadata_cache_uri)
        for did in dids
    ]


@enforce_types_shim
def add_publisher_trusted_algorithm(
    dataset_did: str, algo_did: str, metadata_cache_uri: str
) -> list:
    asset = resolve_asset(dataset_did, metadata_cache_uri=metadata_cache_uri)
    compute_service = asset.get_service(ServiceTypes.CLOUD_COMPUTE)
    assert (
        compute_service
    ), "Cannot add trusted algorithm to this asset because it has no compute service."
    privacy_values = compute_service.attributes["main"].get("privacy")
    if not privacy_values:
        privacy_values = {}
        compute_service.attributes["main"]["privacy"] = privacy_values

    assert isinstance(privacy_values, dict), "Privacy key is not a dictionary."
    trusted_algos = privacy_values.get("publisherTrustedAlgorithms", [])
    # remove algo_did if already in the list
    trusted_algos = [ta for ta in trusted_algos if ta["did"] != algo_did]

    # now add this algo_did as trusted algo
    algo_ddo = resolve_asset(algo_did, metadata_cache_uri=metadata_cache_uri)
    trusted_algos.append(generate_trusted_algo_dict(ddo=algo_ddo))
    # update with the new list
    privacy_values["publisherTrustedAlgorithms"] = trusted_algos
    assert (
        compute_service.attributes["main"]["privacy"] == privacy_values
    ), "New trusted algorithm was not added. Failed when updating the privacy key. "
    return trusted_algos


@enforce_types_shim
def remove_publisher_trusted_algorithm(
    dataset_did: str, algo_did: str, metadata_cache_uri: str
) -> list:
    asset = resolve_asset(dataset_did, metadata_cache_uri=metadata_cache_uri)
    trusted_algorithms = asset.get_trusted_algorithms()
    if not trusted_algorithms:
        raise ValueError(
            f"Algorithm {algo_did} is not in trusted algorithms of this asset."
        )

    trusted_algorithms = [ta for ta in trusted_algorithms if ta["did"] != algo_did]
    asset.update_compute_privacy(trusted_algorithms, False, False)
    assert (
        asset.get_trusted_algorithms() == trusted_algorithms
    ), "New trusted algorithm was not removed. Failed when updating the list of trusted algorithms. "
    return trusted_algorithms
