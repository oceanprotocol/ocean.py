#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import Optional, Union

from enforce_typing import enforce_types
from ocean_lib.assets.asset import V3Asset
from ocean_lib.assets.asset_resolver import resolve_asset
from ocean_lib.assets.v4.asset import V4Asset


@enforce_types
def generate_trusted_algo_dict(
    asset_or_did: Union[str, V3Asset, V4Asset] = None,
    metadata_cache_uri: Optional[str] = None,
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
    if isinstance(asset_or_did, (V3Asset, V4Asset)):
        ddo = asset_or_did
    else:
        ddo = resolve_asset(asset_or_did, metadata_cache_uri=metadata_cache_uri)

    return ddo.generate_trusted_algorithms()


@enforce_types
def create_publisher_trusted_algorithms(
    ddos_or_dids: list, metadata_cache_uri: str
) -> list:
    """
    :return: List of objects returned by `generate_trusted_algo_dict` method.
    """
    return [
        generate_trusted_algo_dict(
            asset_or_did=ddo_or_did, metadata_cache_uri=metadata_cache_uri
        )
        for ddo_or_did in ddos_or_dids
    ]


@enforce_types
def add_publisher_trusted_algorithm(
    asset_or_did: Union[str, V3Asset, V4Asset], algo_did: str, metadata_cache_uri: str
) -> list:
    """
    :return: List of trusted algos
    """
    if isinstance(asset_or_did, (V3Asset, V4Asset)):
        asset = asset_or_did
    else:
        asset = resolve_asset(asset_or_did, metadata_cache_uri=metadata_cache_uri)

    compute_service = asset.get_service("compute")
    assert (
        compute_service
    ), "Cannot add trusted algorithm to this asset because it has no compute service."

    algo_ddo = resolve_asset(algo_did, metadata_cache_uri=metadata_cache_uri)
    generated_trusted_algo_dict = generate_trusted_algo_dict(algo_ddo)

    return compute_service.add_publisher_trusted_algorithm(
        algo_ddo, generated_trusted_algo_dict
    )


@enforce_types
def add_publisher_trusted_algorithm_publisher(
    asset_or_did: Union[str, V3Asset, V4Asset],
    publisher_address: str,
    metadata_cache_uri: str,
) -> list:
    """
    :return: List of trusted algo publishers
    """
    if isinstance(asset_or_did, (V3Asset, V4Asset)):
        asset = asset_or_did
    else:
        asset = resolve_asset(asset_or_did, metadata_cache_uri=metadata_cache_uri)

    compute_service = asset.get_service("compute")
    assert (
        compute_service
    ), "Cannot add trusted algorithm to this asset because it has no compute service."

    return compute_service.add_publisher_trusted_algorithm_publisher(publisher_address)


@enforce_types
def remove_publisher_trusted_algorithm(
    asset_or_did: Union[str, V3Asset, V4Asset], algo_did: str, metadata_cache_uri: str
) -> list:
    """
    :return: List of trusted algos not containing `algo_did`.
    """
    if isinstance(asset_or_did, (V3Asset, V4Asset)):
        asset = asset_or_did
    else:
        asset = resolve_asset(asset_or_did, metadata_cache_uri=metadata_cache_uri)

    compute_service = asset.get_service("compute")
    assert (
        compute_service
    ), "Cannot add trusted algorithm to this asset because it has no compute service."

    return asset.remove_publisher_trusted_algorithm(compute_service, algo_did)


@enforce_types
def remove_publisher_trusted_algorithm_publisher(
    asset_or_did: Union[str, V3Asset, V4Asset],
    publisher_address: str,
    metadata_cache_uri: str,
) -> list:
    """
    :return: List of trusted algo publishers not containing `publisher_address`.
    """
    if isinstance(asset_or_did, (V3Asset, V4Asset)):
        asset = asset_or_did
    else:
        asset = resolve_asset(asset_or_did, metadata_cache_uri=metadata_cache_uri)

    compute_service = asset.get_service("compute")
    assert (
        compute_service
    ), "Cannot add trusted algorithm to this asset because it has no compute service."

    return asset.remove_publisher_trusted_algorithm_publisher(
        compute_service, publisher_address
    )
