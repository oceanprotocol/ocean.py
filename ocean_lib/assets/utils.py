#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import hashlib
import json
from typing import Optional

from enforce_typing import enforce_types
from ocean_lib.assets.asset import Asset
from ocean_lib.assets.asset_resolver import resolve_asset
from ocean_lib.common.agreements.service_types import ServiceTypes


@enforce_types
def create_checksum(text: str) -> str:
    """
    :return: str
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@enforce_types
def generate_trusted_algo_dict(
    did: Optional[str] = None,
    metadata_cache_uri: Optional[str] = None,
    ddo: Optional[Asset] = None,
) -> dict:
    """
    :return: Object as follows:
    ```
    {
        "did": <did>,
        "filesChecksum": <str>,
        "containerSectionChecksum": <str>
    }
    ```
    """
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


@enforce_types
def create_publisher_trusted_algorithms(dids: list, metadata_cache_uri: str) -> list:
    """
    :return: List of objects returned by `generate_trusted_algo_dict` method.
    """
    return [
        generate_trusted_algo_dict(did=did, metadata_cache_uri=metadata_cache_uri)
        for did in dids
    ]


@enforce_types
def add_publisher_trusted_algorithm(
    dataset_did: str, algo_did: str, metadata_cache_uri: str
) -> list:
    """
    :return: List of trusted algos
    """
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


@enforce_types
def add_publisher_trusted_algorithm_publisher(
    dataset_did: str, publisher_address: str, metadata_cache_uri: str
) -> list:
    """
    :return: List of trusted algo publishers
    """
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
    trusted_algo_publishers = privacy_values.get(
        "publisherTrustedAlgorithmPublishers", []
    )

    if publisher_address in trusted_algo_publishers:
        return trusted_algo_publishers

    trusted_algo_publishers.append(publisher_address)
    # update with the new list
    privacy_values["publisherTrustedAlgorithmPublishers"] = trusted_algo_publishers
    assert (
        compute_service.attributes["main"]["privacy"] == privacy_values
    ), "New trusted algorithm was not added. Failed when updating the privacy key. "
    return trusted_algo_publishers


@enforce_types
def remove_publisher_trusted_algorithm(
    dataset_did: str, algo_did: str, metadata_cache_uri: str
) -> list:
    """
    :return: List of trusted algos not containing `algo_did`.
    """
    asset = resolve_asset(dataset_did, metadata_cache_uri=metadata_cache_uri)
    trusted_algorithms = asset.get_trusted_algorithms()
    if not trusted_algorithms:
        raise ValueError(
            f"Algorithm {algo_did} is not in trusted algorithms of this asset."
        )

    trusted_algorithms = [ta for ta in trusted_algorithms if ta["did"] != algo_did]
    trusted_algo_publishers = asset.get_trusted_algorithm_publishers()
    asset.update_compute_privacy(
        trusted_algorithms, trusted_algo_publishers, False, False
    )
    assert (
        asset.get_trusted_algorithms() == trusted_algorithms
    ), "New trusted algorithm was not removed. Failed when updating the list of trusted algorithms. "
    return trusted_algorithms


@enforce_types
def remove_publisher_trusted_algorithm_publisher(
    dataset_did: str, publisher_address: str, metadata_cache_uri: str
) -> list:
    """
    :return: List of trusted algo publishers not containing `publisher_address`.
    """
    asset = resolve_asset(dataset_did, metadata_cache_uri=metadata_cache_uri)
    trusted_algorithm_publishers = asset.get_trusted_algorithm_publishers()
    if not trusted_algorithm_publishers:
        raise ValueError(
            f"Publisher {publisher_address} is not in trusted algorith publishers of this asset."
        )

    trusted_algorithm_publishers.pop(publisher_address)
    trusted_algorithms = asset.get_trusted_algorithms()
    asset.update_compute_privacy(
        trusted_algorithms, trusted_algorithm_publishers, False, False
    )
    assert (
        asset.get_trusted_algorithm_publishers() == trusted_algorithm_publishers
    ), "New trusted algorithm publisher was not removed. Failed when updating the list of trusted algo publishers. "
    return trusted_algorithm_publishers
