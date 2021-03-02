import hashlib
import json

from ocean_utils.agreements.service_types import ServiceTypes


def format_publisher_trusted_algorithms(ocean_asset, trusted_algorithms=None) -> list:
    trusted_algo_list = []
    for trusted_algorithm_did in trusted_algorithms:
        trusted_algorithm_ddo = ocean_asset.resolve(
            trusted_algorithm_did
        )  # but what if served by different provider?
        alg_crt_service = trusted_algorithm_ddo.get_service(ServiceTypes.METADATA)
        trusted_algo_list.append(
            {
                "did": trusted_algorithm_did,
                "filesChecksum": hashlib.sha256(
                    (
                        alg_crt_service.attributes["encryptedFiles"]
                        + json.dumps(alg_crt_service.main["files"])
                    ).encode("utf-8")
                ).hexdigest(),
                "containerSectionChecksum": hashlib.sha256(
                    (json.dumps(alg_crt_service.main["algorithm"]["container"])).encode(
                        "utf-8"
                    )
                ).hexdigest(),
            }
        )
    return trusted_algo_list
