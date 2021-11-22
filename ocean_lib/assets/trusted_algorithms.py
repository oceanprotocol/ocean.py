#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json
from typing import Optional, Union

from enforce_typing import enforce_types
from ocean_lib.assets.asset import V3Asset
from ocean_lib.assets.asset_resolver import resolve_asset
from ocean_lib.assets.v4.asset import V4Asset
from ocean_lib.utils.utilities import create_checksum


@enforce_types
def generate_trusted_algo_dict(
    asset_or_did: Union[str, V3Asset] = None, metadata_cache_uri: Optional[str] = None
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
    if isinstance(asset_or_did, V3Asset):
        ddo = asset_or_did
    else:
        ddo = resolve_asset(asset_or_did, metadata_cache_uri=metadata_cache_uri)

    algo_metadata = ddo.metadata
    return {
        "did": ddo.did,
        "filesChecksum": create_checksum(
            algo_metadata.get("encryptedFiles", "")
            + json.dumps(algo_metadata["main"]["files"], separators=(",", ":"))
        ),
        "containerSectionChecksum": create_checksum(
            json.dumps(
                algo_metadata["main"]["algorithm"]["container"], separators=(",", ":")
            )
        ),
    }


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
    if isinstance(asset_or_did, V3Asset) or isinstance(asset_or_did, V4Asset):
        asset = asset_or_did
    else:
        asset = resolve_asset(asset_or_did, metadata_cache_uri=metadata_cache_uri)

    compute_service = asset.get_service("compute")
    assert (
        compute_service
    ), "Cannot add trusted algorithm to this asset because it has no compute service."

    if asset.version:
        initial_trusted_algos_v4 = compute_service.get_trusted_algos_v4()
        # remove algo_did if already in the list
        trusted_algos = [ta for ta in initial_trusted_algos_v4 if ta["did"] != algo_did]
        algo_ddo = resolve_asset(algo_did, metadata_cache_uri=metadata_cache_uri)
        trusted_algos.append(generate_trusted_algo_dict(asset_or_did=algo_ddo))

        # update with the new list
        compute_service.compute_values["publisherTrustedAlgorithms"] = trusted_algos
        assert len(compute_service.compute_values["publisherTrustedAlgorithms"]) > len(
            initial_trusted_algos_v4
        ), "New trusted algorithm was not added. Failed when updating the privacy key. "
    else:
        initial_trusted_algos_v3 = compute_service.get_trusted_algos()

        # remove algo_did if already in the list
        trusted_algos = [ta for ta in initial_trusted_algos_v3 if ta["did"] != algo_did]

        # now add this algo_did as trusted algo
        algo_ddo = resolve_asset(algo_did, metadata_cache_uri=metadata_cache_uri)
        trusted_algos.append(generate_trusted_algo_dict(asset_or_did=algo_ddo))

        # update with the new list
        compute_service.attributes["main"]["privacy"][
            "publisherTrustedAlgorithms"
        ] = trusted_algos
        assert len(compute_service.attributes["main"]["privacy"]) > len(
            initial_trusted_algos_v3
        ), "New trusted algorithm was not added. Failed when updating the privacy key. "

    return trusted_algos


@enforce_types
def add_publisher_trusted_algorithm_publisher(
    asset_or_did: Union[str, V3Asset, V4Asset],
    publisher_address: str,
    metadata_cache_uri: str,
) -> list:
    """
    :return: List of trusted algo publishers
    """
    if isinstance(asset_or_did, V3Asset) or isinstance(asset_or_did, V4Asset):
        asset = asset_or_did
    else:
        asset = resolve_asset(asset_or_did, metadata_cache_uri=metadata_cache_uri)

    compute_service = asset.get_service("compute")
    assert (
        compute_service
    ), "Cannot add trusted algorithm to this asset because it has no compute service."

    if asset.version:
        return compute_service.add_trusted_algo_publisher_v4(
            new_publisher_address=publisher_address
        )
    else:
        return compute_service.add_trusted_algo_publisher(
            new_publisher_address=publisher_address
        )


@enforce_types
def remove_publisher_trusted_algorithm(
    asset_or_did: Union[str, V3Asset], algo_did: str, metadata_cache_uri: str
) -> list:
    """
    :return: List of trusted algos not containing `algo_did`.
    """
    if isinstance(asset_or_did, V3Asset):
        asset = asset_or_did
    else:
        asset = resolve_asset(asset_or_did, metadata_cache_uri=metadata_cache_uri)

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
    asset_or_did: Union[str, V3Asset], publisher_address: str, metadata_cache_uri: str
) -> list:
    """
    :return: List of trusted algo publishers not containing `publisher_address`.
    """
    if isinstance(asset_or_did, V3Asset):
        asset = asset_or_did
    else:
        asset = resolve_asset(asset_or_did, metadata_cache_uri=metadata_cache_uri)

    trusted_algorithm_publishers = [
        tp.lower() for tp in asset.get_trusted_algorithm_publishers()
    ]
    publisher_address = publisher_address.lower()

    if not trusted_algorithm_publishers:
        raise ValueError(
            f"Publisher {publisher_address} is not in trusted algorith publishers of this asset."
        )

    trusted_algorithm_publishers = [
        tp for tp in trusted_algorithm_publishers if tp != publisher_address
    ]
    trusted_algorithms = asset.get_trusted_algorithms()
    asset.update_compute_privacy(
        trusted_algorithms, trusted_algorithm_publishers, False, False
    )
    assert (
        asset.get_trusted_algorithm_publishers() == trusted_algorithm_publishers
    ), "New trusted algorithm publisher was not removed. Failed when updating the list of trusted algo publishers. "
    return trusted_algorithm_publishers
