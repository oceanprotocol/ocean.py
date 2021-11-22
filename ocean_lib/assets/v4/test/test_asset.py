#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

from ocean_lib.assets.v4.asset import V4Asset
from ocean_lib.common.agreements.service_types import ServiceTypesV4
from ocean_lib.services.v4.service import V4Service
from tests.resources.ddo_helpers import (
    get_key_from_v4_sample_ddo,
    get_sample_v4_ddo,
    get_sample_v4_ddo_with_compute_service,
)

ENCRYPTED_FILES_URLS = "0x044736da6dae39889ff570c34540f24e5e084f4e5bd81eff3691b729c2dd1465ae8292fc721e9d4b1f10f56ce12036c9d149a4dab454b0795bd3ef8b7722c6001e0becdad5caeb2005859642284ef6a546c7ed76f8b350480691f0f6c6dfdda6c1e4d50ee90e83ce3cb3ca0a1a5a2544e10daa6637893f4276bb8d7301eb35306ece50f61ca34dcab550b48181ec81673953d4eaa4b5f19a45c0e9db4cd9729696f16dd05e0edb460623c843a263291ebe757c1eb3435bb529cc19023e0f49db66ef781ca692655992ea2ca7351ac2882bf340c9d9cb523b0cbcd483731dc03f6251597856afa9a68a1e0da698cfc8e81824a69d92b108023666ee35de4a229ad7e1cfa9be9946db2d909735"


def test_asset_utils(web3):
    """Tests the structure of a JSON format of the V4 Asset."""
    ddo_dict = get_sample_v4_ddo()
    assert isinstance(ddo_dict, dict)

    assert isinstance(ddo_dict, dict)
    assert ddo_dict["@context"] == ["https://w3id.org/did/v1"]
    context = ddo_dict["@context"]
    assert ddo_dict["id"] == "did:op:ACce67694eD2848dd683c651Dab7Af823b7dd123"
    did = ddo_dict["id"]
    assert ddo_dict["version"] == "4.0.0"
    assert ddo_dict["chainId"] == web3.eth.chain_id
    chain_id = ddo_dict["chainId"]

    assert ddo_dict["metadata"] == {
        "created": "2020-11-15T12:27:48Z",
        "updated": "2021-05-17T21:58:02Z",
        "description": "Sample description",
        "name": "Sample asset",
        "type": "dataset",
        "author": "OPF",
        "license": "https://market.oceanprotocol.com/terms",
    }
    metadata = ddo_dict["metadata"]
    assert isinstance(ddo_dict["services"], list)
    assert ddo_dict["services"] == [
        {
            "serviceId": "1",
            "type": "access",
            "files": ENCRYPTED_FILES_URLS,
            "name": "Download service",
            "description": "Download service",
            "datatokenAddress": "0x123",
            "serviceEndpoint": "https://myprovider.com",
            "timeout": 0,
        }
    ]
    services = ddo_dict["services"]

    assert ddo_dict["credentials"] == {
        "allow": [{"type": "address", "values": ["0x123", "0x456"]}],
        "deny": [{"type": "address", "values": ["0x2222", "0x333"]}],
    }
    credentials = ddo_dict["credentials"]

    assert ddo_dict["nft"] == {
        "address": "0x000000",
        "name": "Ocean Protocol Asset v4",
        "symbol": "OCEAN-A-v4",
        "owner": "0x0000000",
        "state": 0,
        "created": "2000-10-31T01:30:00",
    }
    nft = ddo_dict["nft"]

    assert ddo_dict["datatokens"] == [
        {
            "address": "0x000000",
            "name": "Datatoken 1",
            "symbol": "DT-1",
            "serviceId": "1",
        }
    ]
    data_tokens = ddo_dict["datatokens"]

    assert ddo_dict["event"] == {
        "tx": "0x8d127de58509be5dfac600792ad24cc9164921571d168bff2f123c7f1cb4b11c",
        "block": 12831214,
        "from": "0xAcca11dbeD4F863Bb3bC2336D3CE5BAC52aa1f83",
        "contract": "0x1a4b70d8c9DcA47cD6D0Fb3c52BB8634CA1C0Fdf",
        "datetime": "2000-10-31T01:30:00",
    }
    event = ddo_dict["event"]

    assert ddo_dict["stats"] == {"consumes": 4, "isInPurgatory": "false"}
    stats = ddo_dict["stats"]

    ddo = V4Asset(
        did=did,
        context=context,
        chain_id=chain_id,
        metadata=metadata,
        services=services,
        credentials=credentials,
        nft=nft,
        datatokens=data_tokens,
        event=event,
        stats=stats,
    )
    ddo_dict_v2 = ddo.as_dictionary()

    ddo_v2 = V4Asset.from_dict(ddo_dict_v2)
    assert ddo_v2.as_dictionary() == ddo_dict


def test_add_service():
    """Tests adding a compute service."""

    ddo_dict = get_sample_v4_ddo()
    ddo = V4Asset.from_dict(ddo_dict)
    compute_values = {
        "namespace": "ocean-compute",
        "cpus": 2,
        "gpus": 4,
        "gpuType": "NVIDIA Tesla V100 GPU",
        "memory": "128M",
        "volumeSize": "2G",
        "allowRawAlgorithm": False,
        "allowNetworkAccess": True,
        "publisherTrustedAlgorithmPublishers": ["0x234", "0x235"],
        "publisherTrustedAlgorithms": [
            {
                "did": "did:op:123",
                "filesChecksum": "100",
                "containerSectionChecksum": "200",
            },
            {
                "did": "did:op:124",
                "filesChecksum": "110",
                "containerSectionChecksum": "210",
            },
        ],
    }
    new_service = V4Service(
        service_id="2",
        service_type="compute",
        service_endpoint="https://myprovider.com",
        data_token="0x124",
        files=ENCRYPTED_FILES_URLS,
        timeout=3600,
        compute_values=compute_values,
        name="Compute service",
        description="Compute service",
    )
    ddo.add_service(new_service)
    assert len(ddo.as_dictionary()["services"]) > 1

    expected_access_service = get_key_from_v4_sample_ddo(
        key="services", file_name="ddo_v4_with_compute_service.json"
    )[0]
    assert ddo.as_dictionary()["services"][0] == expected_access_service

    expected_compute_service = get_key_from_v4_sample_ddo(
        key="services", file_name="ddo_v4_with_compute_service.json"
    )[1]

    assert (
        ddo.as_dictionary()["services"][1]["serviceId"]
        == expected_compute_service["serviceId"]
    )

    assert (
        ddo.as_dictionary()["services"][1]["name"] == expected_compute_service["name"]
    )
    assert (
        ddo.as_dictionary()["services"][1]["description"]
        == expected_compute_service["description"]
    )
    assert (
        ddo.as_dictionary()["services"][1]["serviceEndpoint"]
        == expected_compute_service["serviceEndpoint"]
    )
    assert (
        ddo.as_dictionary()["services"][1]["datatokenAddress"]
        == expected_compute_service["datatokenAddress"]
    )
    assert (
        ddo.as_dictionary()["services"][1]["files"] == expected_compute_service["files"]
    )
    assert (
        ddo.as_dictionary()["services"][1]["timeout"]
        == expected_compute_service["timeout"]
    )
    assert (
        ddo.as_dictionary()["services"][1]["compute"]
        == expected_compute_service["compute"]
    )


def test_get_service():
    """Tests retrieving services from the V4 DDO."""
    ddo_dict = get_sample_v4_ddo_with_compute_service()
    ddo = V4Asset.from_dict(ddo_dict)
    expected_access_service = get_key_from_v4_sample_ddo(
        key="services", file_name="ddo_v4_with_compute_service.json"
    )[0]

    assert (
        ddo.get_service(ServiceTypesV4.ASSET_ACCESS).as_dictionary()
        == expected_access_service
    )
    assert ddo.get_service_by_id("1").as_dictionary() == expected_access_service

    expected_compute_service = get_key_from_v4_sample_ddo(
        key="services", file_name="ddo_v4_with_compute_service.json"
    )[1]
    assert ddo.get_service_by_id("2").as_dictionary() == expected_compute_service
    assert (
        ddo.get_service(ServiceTypesV4.CLOUD_COMPUTE).as_dictionary()
        == expected_compute_service
    )
