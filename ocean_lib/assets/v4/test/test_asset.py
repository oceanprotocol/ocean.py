#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_lib.assets.v4.asset import V4Asset
from tests.resources.ddo_helpers import get_key_from_v4_sample_ddo, get_sample_v4_ddo


def test_get_asset_as_dict(web3):
    """Tests the structure of a JSON format of the V4 Asset."""
    ddo = get_sample_v4_ddo()
    assert isinstance(ddo, V4Asset)
    ddo_dict = ddo.as_dictionary()

    assert isinstance(ddo_dict, dict)
    assert ddo_dict["@context"] == ["https://w3id.org/did/v1"]
    assert ddo_dict["id"] == "did:op:ACce67694eD2848dd683c651Dab7Af823b7dd123"
    assert ddo_dict["version"] == "4.0.0"
    assert ddo_dict["chainId"] == web3.eth.chain_id

    assert ddo_dict["metadata"] == {
        "created": "2020-11-15T12:27:48Z",
        "updated": "2021-05-17T21:58:02Z",
        "description": "Sample description",
        "name": "Sample asset",
        "type": "dataset",
        "author": "OPF",
        "license": "https://market.oceanprotocol.com/terms",
    }
    assert isinstance(ddo_dict["services"], list)
    assert ddo_dict["services"] == [
        {
            "type": "access",
            "files": "0x044736da6dae39889ff570c34540f24e5e084f4e5bd81eff3691b729c2dd1465ae8292fc721e9d4b1f10f56ce12036c9d149a4dab454b0795bd3ef8b7722c6001e0becdad5caeb2005859642284ef6a546c7ed76f8b350480691f0f6c6dfdda6c1e4d50ee90e83ce3cb3ca0a1a5a2544e10daa6637893f4276bb8d7301eb35306ece50f61ca34dcab550b48181ec81673953d4eaa4b5f19a45c0e9db4cd9729696f16dd05e0edb460623c843a263291ebe757c1eb3435bb529cc19023e0f49db66ef781ca692655992ea2ca7351ac2882bf340c9d9cb523b0cbcd483731dc03f6251597856afa9a68a1e0da698cfc8e81824a69d92b108023666ee35de4a229ad7e1cfa9be9946db2d909735",
            "name": "Download service",
            "description": "Download service",
            "datatokenAddress": "0x123",
            "serviceEndpoint": "https://myprovider.com",
            "timeout": 0,
        }
    ]

    assert ddo_dict["credentials"] == {
        "allow": [{"type": "address", "values": ["0x123", "0x456"]}],
        "deny": [{"type": "address", "values": ["0x2222", "0x333"]}],
    }

    assert ddo_dict["nft"] == {
        "address": "0x000000",
        "name": "Ocean Protocol Asset v4",
        "symbol": "OCEAN-A-v4",
        "owner": "0x0000000",
        "state": 0,
        "created": "2000-10-31T01:30:00",
    }

    assert ddo_dict["datatokens"] == [
        {
            "address": "0x000000",
            "name": "Datatoken 1",
            "symbol": "DT-1",
            "serviceId": "1",
        },
        {
            "address": "0x000001",
            "name": "Datatoken 2",
            "symbol": "DT-2",
            "serviceId": "2",
        },
    ]

    assert ddo_dict["event"] == {
        "tx": "0x8d127de58509be5dfac600792ad24cc9164921571d168bff2f123c7f1cb4b11c",
        "block": 12831214,
        "from": "0xAcca11dbeD4F863Bb3bC2336D3CE5BAC52aa1f83",
        "contract": "0x1a4b70d8c9DcA47cD6D0Fb3c52BB8634CA1C0Fdf",
        "datetime": "2000-10-31T01:30:00",
    }

    assert ddo_dict["stats"] == {"consumes": 4, "isInPurgatory": "false"}


def test_properties():
    """Tests the properties for V4 Asset."""
    ddo = get_sample_v4_ddo()
    assert ddo.chain_id == 1337

    assert ddo.metadata == get_key_from_v4_sample_ddo("metadata")
    assert (
        ddo.allowed_addresses
        == get_key_from_v4_sample_ddo("credentials")["allow"][0]["values"]
    )
    assert (
        ddo.denied_addresses
        == get_key_from_v4_sample_ddo("credentials")["deny"][0]["values"]
    )

    assert ddo.asset_id == ddo.did.replace("did:op:", "0x", 1)
    assert ddo.services[0].as_dictionary() == get_key_from_v4_sample_ddo("services")[0]
