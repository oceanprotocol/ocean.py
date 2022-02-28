#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest

from ocean_lib.agreements.consumable import MalformedCredential
from ocean_lib.assets.asset import Asset
from ocean_lib.assets.credentials import simplify_credential_to_address
from ocean_lib.services.service import Service
from tests.resources.ddo_helpers import (
    get_key_from_v4_sample_ddo,
    get_sample_ddo,
    get_sample_ddo_with_compute_service,
)


@pytest.mark.unit
def test_asset_utils(web3):
    """Tests the structure of a JSON format of the V4 Asset."""
    ddo_dict = get_sample_ddo()
    assert isinstance(ddo_dict, dict)

    assert isinstance(ddo_dict, dict)
    assert ddo_dict["@context"] == ["https://w3id.org/did/v1"]
    context = ddo_dict["@context"]
    assert (
        ddo_dict["id"]
        == "did:op:68a7f03e59c70d59607e3f0a536ed4d32e0599db07f587d66bd1221573d38c21"
    )
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
            "id": "1",
            "type": "access",
            "files": "0x0000",
            "name": "Download service",
            "description": "Download service",
            "datatokenAddress": "0x123",
            "serviceEndpoint": "https://myprovider.com",
            "timeout": 0,
        }
    ]

    services = [
        Service.from_dict(value)
        for value in ddo_dict["services"]
        if isinstance(value, dict)
    ]

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
    datatokens = ddo_dict["datatokens"]

    assert ddo_dict["event"] == {
        "tx": "0x8d127de58509be5dfac600792ad24cc9164921571d168bff2f123c7f1cb4b11c",
        "block": 12831214,
        "from": "0xAcca11dbeD4F863Bb3bC2336D3CE5BAC52aa1f83",
        "contract": "0x1a4b70d8c9DcA47cD6D0Fb3c52BB8634CA1C0Fdf",
        "datetime": "2000-10-31T01:30:00",
    }
    event = ddo_dict["event"]

    # Sample asset
    assert ddo_dict["stats"] == {"consumes": 4}
    stats = ddo_dict["stats"]

    ddo = Asset(
        did=did,
        context=context,
        chain_id=chain_id,
        metadata=metadata,
        services=services,
        credentials=credentials,
        nft=nft,
        nft_address="0xabc",
        datatokens=datatokens,
        event=event,
        stats=stats,
    )
    ddo_dict_v2 = ddo.as_dictionary()

    ddo_v2 = Asset.from_dict(ddo_dict_v2)
    assert ddo_v2.as_dictionary() == ddo_dict


@pytest.mark.unit
def test_add_service():
    """Tests adding a compute service."""

    ddo_dict = get_sample_ddo()
    ddo = Asset.from_dict(ddo_dict)
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
    new_service = Service(
        service_id="2",
        service_type="compute",
        service_endpoint="https://myprovider.com",
        datatoken="0x124",
        files="0x0001",
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

    assert ddo.as_dictionary()["services"][1]["id"] == expected_compute_service["id"]

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


@pytest.mark.unit
def test_get_service_by_id():
    """Tests retrieving services from the V4 DDO."""
    ddo_dict = get_sample_ddo_with_compute_service()
    ddo = Asset.from_dict(ddo_dict)
    expected_access_service = get_key_from_v4_sample_ddo(
        key="services", file_name="ddo_v4_with_compute_service.json"
    )[0]

    assert ddo.get_service_by_id("1").as_dictionary() == expected_access_service

    expected_compute_service = get_key_from_v4_sample_ddo(
        key="services", file_name="ddo_v4_with_compute_service.json"
    )[1]
    assert ddo.get_service_by_id("2").as_dictionary() == expected_compute_service


@pytest.mark.unit
def test_credentials():
    ddo_dict = get_sample_ddo_with_compute_service()
    ddo = Asset.from_dict(ddo_dict)
    assert ddo.requires_address_credential
    assert ddo.allowed_addresses == ["0x123", "0x456"]
    assert ddo.denied_addresses == ["0x2222", "0x333"]

    ddo.add_address_to_allow_list("0xaAA")
    assert "0xaaa" in ddo.allowed_addresses
    ddo.remove_address_from_allow_list("0xaAA")
    assert "0xaaa" not in ddo.allowed_addresses
    ddo.remove_address_from_allow_list("0xaAA")

    ddo.add_address_to_deny_list("0xaAA")
    assert "0xaaa" in ddo.denied_addresses
    ddo.remove_address_from_deny_list("0xaAA")
    assert "0xaaa" not in ddo.denied_addresses

    assert ddo.validate_access({"type": "address", "value": "0x123"}) == 0
    # not allowed
    assert ddo.validate_access({"type": "address", "value": "0x444"}) == 3

    ddo_dict = get_sample_ddo_with_compute_service()
    del ddo_dict["credentials"]["allow"]
    ddo = Asset.from_dict(ddo_dict)
    assert ddo.validate_access({"type": "address", "value": "0x444"}) == 0
    # specifically denied
    assert ddo.validate_access({"type": "address", "value": "0x333"}) == 4

    ddo_dict = get_sample_ddo_with_compute_service()
    del ddo_dict["credentials"]["allow"][0]["values"]
    ddo = Asset.from_dict(ddo_dict)
    with pytest.raises(
        MalformedCredential, match="No values key in the address credential"
    ):
        ddo.get_addresses_of_class("allow")

    ddo_dict = get_sample_ddo_with_compute_service()
    del ddo_dict["credentials"]
    ddo = Asset.from_dict(ddo_dict)
    ddo.remove_address_from_allow_list("0xAA")
    ddo.add_address_to_allow_list("0xAA")

    ddo_dict = get_sample_ddo_with_compute_service()
    ddo_dict["credentials"]["allow"] = []
    ddo = Asset.from_dict(ddo_dict)
    ddo.remove_address_from_allow_list("0xAA")
    ddo.add_address_to_allow_list("0xAA")


@pytest.mark.unit
def test_credential_simplification():
    assert simplify_credential_to_address(None) is None
    with pytest.raises(MalformedCredential, match="Received empty address."):
        simplify_credential_to_address({"malformed": "no value"})
    assert (
        simplify_credential_to_address({"type": "address", "value": "0x11"}) == "0x11"
    )
