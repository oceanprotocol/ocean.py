import hashlib
import json

from ocean_utils.agreements.service_types import ServiceTypes


def create_publisher_trusted_algorithms(ocean_asset, trusted_algorithms) -> list:
    trusted_algo_list = []
    for trusted_algorithm_did in trusted_algorithms:
        trusted_algorithm_ddo = ocean_asset.resolve(
            trusted_algorithm_did
        )  # but what if served by different provider?
        algo_metadata = trusted_algorithm_ddo.metadata
        trusted_algo_list.append(
            {
                "did": trusted_algorithm_did,
                "filesChecksum": hashlib.sha256(
                    (
                        algo_metadata["encryptedFiles"]
                        + json.dumps(algo_metadata["main"]["files"])
                    ).encode("utf-8")
                ).hexdigest(),
                "containerSectionChecksum": hashlib.sha256(
                    (
                        json.dumps(algo_metadata["main"]["algorithm"]["container"])
                    ).encode("utf-8")
                ).hexdigest(),
            }
        )
    return trusted_algo_list


def add_publisher_trusted_algorithm(
    ocean_asset, algo_did: str = None, trusted_algorithms=None
) -> list:
    trusted_algorithms = create_publisher_trusted_algorithms(
        ocean_asset, trusted_algorithms=trusted_algorithms
    )
    assert trusted_algorithms
    algo_ddo = None
    if not ocean_asset:
        algo_ddo = ocean_asset.resolve(algo_did)
    service = algo_ddo.get_service(ServiceTypes.METADATA)
    trusted_algorithm = {
        "did": algo_did,
        "filesChecksum": hashlib.sha256(
            (
                service.attributes["encryptedFiles"] + json.dumps(service.main["files"])
            ).encode("utf-8")
        ).hexdigest(),
        "containerSectionChecksum": hashlib.sha256(
            (json.dumps(service.main["algorithm"]["container"])).encode("utf-8")
        ).hexdigest(),
    }
    if trusted_algorithm:
        trusted_algorithms.append(trusted_algorithm)
    return trusted_algorithms


def remove_publisher_trusted_algorithm(
    ocean_asset, algo_did: str = None, trusted_algorithms=None
) -> list:
    trusted_algorithms = create_publisher_trusted_algorithms(
        ocean_asset, trusted_algorithms=trusted_algorithms
    )
    assert trusted_algorithms, algo_did
    trusted_algorithms = filter(lambda x: x.did != algo_did, trusted_algorithms)
    return list(trusted_algorithms)
