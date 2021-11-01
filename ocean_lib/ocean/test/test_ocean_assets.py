#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import time
import uuid
from unittest.mock import patch

import pytest
from eth_utils import add_0x_prefix
from ocean_lib.assets.asset import V3Asset
from ocean_lib.assets.did import DID, did_to_id
from ocean_lib.common.agreements.consumable import ConsumableCodes
from ocean_lib.exceptions import InsufficientBalance
from ocean_lib.models.data_token import DataToken
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from tests.resources.ddo_helpers import (
    get_computing_metadata,
    get_resource_path,
    get_sample_algorithm_ddo_dict,
    get_sample_ddo,
    wait_for_ddo,
    wait_for_update,
)
from tests.resources.helper_functions import get_consumer_wallet, get_publisher_wallet


def create_asset(ocean, publisher, encrypt=False):
    """Helper function for asset creation based on ddo_sa_sample.json."""
    sample_ddo_path = get_resource_path("ddo", "ddo_sa_sample.json")
    assert sample_ddo_path.exists(), "{} does not exist!".format(sample_ddo_path)

    asset = V3Asset(json_filename=sample_ddo_path)
    asset.metadata["main"]["files"][0]["checksum"] = str(uuid.uuid4())
    return ocean.assets.create(asset.metadata, publisher, [], encrypt=encrypt)


@pytest.mark.parametrize("encrypt", [False, True])
def test_register_asset(publisher_ocean_instance, encrypt):
    """Test various paths for asset registration."""
    ocn = publisher_ocean_instance
    ddo_reg = ocn.assets.ddo_registry()
    block = ocn.web3.eth.block_number
    alice = get_publisher_wallet()
    bob = get_consumer_wallet()

    def _get_num_assets(_minter):
        dids = [add_0x_prefix(did_to_id(a)) for a in ocn.assets.owner_assets(_minter)]
        dids = [a for a in dids if len(a) == 42]
        return len(
            [
                a
                for a in dids
                if DataToken(ocn.web3, a).contract.caller.isMinter(_minter)
            ]
        )

    num_assets_owned = _get_num_assets(alice.address)

    original_ddo = create_asset(ocn, alice, encrypt=encrypt)
    assert original_ddo, "create asset failed."

    # try to resolve new asset
    did = original_ddo.did
    asset_id = original_ddo.asset_id
    block_confirmations = ocn.config.block_confirmations.value
    log = ddo_reg.get_event_log(
        ddo_reg.EVENT_METADATA_CREATED, block - (block_confirmations + 1), asset_id, 30
    )
    assert log, "no ddo created event."

    ddo = wait_for_ddo(ocn, did)
    assert ddo, "ddo is not found in cache."
    ddo_dict = ddo.as_dictionary()
    original = original_ddo.as_dictionary()
    assert (
        ddo_dict["publicKey"] == original["publicKey"]
    ), "The new asset's public key does not coincide with the original asset's one."
    assert (
        ddo_dict["authentication"] == original["authentication"]
    ), "The new asset's authentication key does not coincide with the original asset's one."
    assert ddo_dict["service"], "The new asset does not have the service field."
    assert original["service"], "The original asset does not have the service field."
    metadata = ddo_dict["service"][0]["attributes"]
    if "datePublished" in metadata["main"]:
        metadata["main"].pop("datePublished")
    assert (
        ddo_dict["service"][0]["attributes"]["main"]["name"]
        == original["service"][0]["attributes"]["main"]["name"]
    ), "The new asset has a different name."
    assert (
        ddo_dict["service"][1] == original["service"][1]
    ), "The new asset's access service does not coincide with the original asset's one."

    # Can't resolve unregistered asset
    unregistered_did = DID.did({"0": "0x00112233445566"})
    assert ocn.assets.resolve(unregistered_did) is None

    invalid_did = "did:op:0123456789"
    assert ocn.assets.resolve(invalid_did) is None

    meta_data_assets = ocn.assets.search("")
    if meta_data_assets:
        print("Currently registered assets:")
        print(meta_data_assets)

    # Publish the metadata
    _name = "updated name"
    ddo.metadata["main"]["name"] = _name
    assert ddo.metadata["main"]["name"] == _name, "Asset's name was not updated."
    with pytest.raises(ValueError):
        ocn.assets.update(ddo, bob)

    _ = ocn.assets.update(ddo, alice, encrypt=encrypt)
    block_confirmations = ocn.config.block_confirmations.value
    log = ddo_reg.get_event_log(
        ddo_reg.EVENT_METADATA_UPDATED, block - block_confirmations, asset_id, 30
    )
    assert log, "no ddo updated event"
    _asset = wait_for_update(ocn, ddo.did, "name", _name)
    assert _asset, "Cannot read asset after update."
    assert (
        _asset.metadata["main"]["name"] == _name
    ), "updated asset does not have the new updated name !!!"

    assert (
        ocn.assets.owner(ddo.did) == alice.address
    ), "asset owner does not seem correct."

    assert (
        _get_num_assets(alice.address) == num_assets_owned + 1
    ), "The new asset was not published in Alice wallet."


def test_ocean_assets_search(publisher_ocean_instance, metadata):
    """Tests that a created asset can be searched successfully."""
    identifier = str(uuid.uuid1()).replace("-", "")
    metadata_copy = metadata.copy()
    metadata_copy["main"]["name"] = identifier
    assert (
        len(publisher_ocean_instance.assets.search(identifier)) == 0
    ), "Asset search failed."

    publisher = get_publisher_wallet()
    ddo = publisher_ocean_instance.assets.create(metadata_copy, publisher)
    wait_for_ddo(publisher_ocean_instance, ddo.did)
    time.sleep(1)  # apparently changes are not instantaneous
    assert (
        len(publisher_ocean_instance.assets.search(identifier)) == 1
    ), "Searched for the occurrences of the identifier failed. "
    assert (
        len(
            publisher_ocean_instance.assets.query(
                {
                    "query": {
                        "query_string": {
                            "query": identifier,
                            "fields": ["service.attributes.main.name"],
                        }
                    }
                }
            )
        )
        == 1
    ), "Query failed.The identifier was not found in the name."
    assert (
        len(
            publisher_ocean_instance.assets.query(
                {
                    "query": {
                        "query_string": {
                            "query": "Gorilla",
                            "fields": ["service.attributes.main.name"],
                        }
                    }
                }
            )
        )
        == 0
    )


def test_ocean_assets_validate(publisher_ocean_instance, metadata):
    """Tests that the validate function returns an error for invalid metadata."""
    assert publisher_ocean_instance.assets.validate(
        metadata
    ), "metadata should be valid, unless the schema changed."


def test_ocean_assets_algorithm(publisher_ocean_instance):
    """Tests the creation of an algorithm DDO."""
    publisher = get_publisher_wallet()
    metadata = get_sample_algorithm_ddo_dict()["service"][0]
    metadata["attributes"]["main"]["files"][0]["checksum"] = str(uuid.uuid4())
    ddo = publisher_ocean_instance.assets.create(metadata["attributes"], publisher)
    assert ddo, "DDO None. The ddo is not cached after the creation."
    _ddo = wait_for_ddo(publisher_ocean_instance, ddo.did)
    assert _ddo, f"assets.resolve failed for did {ddo.did}"
    assert _ddo.is_consumable() == ConsumableCodes.OK


def test_ocean_assets_create_fails_fileinfo(publisher_ocean_instance):
    """Tests that a file with invalid URL can not be published."""
    publisher = get_publisher_wallet()
    metadata = get_sample_algorithm_ddo_dict()["service"][0]
    metadata["attributes"]["main"]["files"][0]["checksum"] = str(uuid.uuid4())
    metadata_copy = metadata.copy()
    metadata_copy["attributes"]["main"]["files"][0][
        "url"
    ] = "http://127.0.0.1/not_valid"
    with pytest.raises(ValueError):
        publisher_ocean_instance.assets.create(metadata_copy["attributes"], publisher)


def test_ocean_assets_compute(publisher_ocean_instance):
    """Tests the creation of an asset with a compute service."""
    publisher = get_publisher_wallet()
    metadata = get_computing_metadata()
    metadata["main"]["files"][0]["checksum"] = str(uuid.uuid4())
    ddo = publisher_ocean_instance.assets.create(metadata, publisher)
    assert ddo, "DDO None. The ddo is not cached after the creation."
    _ddo = wait_for_ddo(publisher_ocean_instance, ddo.did)
    assert _ddo, f"assets.resolve failed for did {ddo.did}"


def test_download_fails(publisher_ocean_instance):
    """Tests failures of assets download function."""
    publisher = get_publisher_wallet()
    with patch("ocean_lib.ocean.ocean_assets.OceanAssets.resolve") as mock:
        mock.return_value = get_sample_ddo()
        with pytest.raises(AssertionError):
            publisher_ocean_instance.assets.download("0x1", 1, publisher, "", "", -4)
        with pytest.raises(TypeError):
            publisher_ocean_instance.assets.download(
                "0x1", "", publisher, "", "", "string_index"
            )


def test_create_bad_metadata(publisher_ocean_instance):
    """Tests that we can't create the asset with plecos failure."""
    publisher = get_publisher_wallet()
    metadata = get_sample_algorithm_ddo_dict()["service"][0]
    metadata["attributes"]["main"]["files"][0]["EXTRA ATTRIB!"] = 0
    with pytest.raises(ValueError):
        publisher_ocean_instance.assets.create(metadata["attributes"], publisher)


def test_create_asset_with_address(publisher_ocean_instance):
    """Tests that an asset can be created with specific DT address."""
    ocn = publisher_ocean_instance
    alice = get_publisher_wallet()

    sample_ddo_path = get_resource_path("ddo", "ddo_sa_sample.json")
    asset = V3Asset(json_filename=sample_ddo_path)
    asset.metadata["main"]["files"][0]["checksum"] = str(uuid.uuid4())

    token = ocn.create_data_token(
        "DataToken1", "DT1", from_wallet=alice, blob="foo_blob"
    )

    assert ocn.assets.create(
        asset.metadata, alice, [], data_token_address=token.address
    ), "Asset creation failed with the specified datatoken address."


def test_create_asset_with_owner_address(publisher_ocean_instance):
    """Tests that an asset can be created with owner address."""
    ocn = publisher_ocean_instance
    alice = get_publisher_wallet()

    sample_ddo_path = get_resource_path("ddo", "ddo_sa_sample.json")
    asset = V3Asset(json_filename=sample_ddo_path)
    asset.metadata["main"]["files"][0]["checksum"] = str(uuid.uuid4())

    assert ocn.assets.create(
        asset.metadata, alice, [], owner_address=alice.address
    ), "Asset creation failed with the specified owner address."


def test_create_asset_with_dt_address_and_owner_address(publisher_ocean_instance):
    """Tests that an asset can be created with both a datatoken address and owner address."""
    ocn = publisher_ocean_instance
    alice = get_publisher_wallet()

    sample_ddo_path = get_resource_path("ddo", "ddo_sa_sample.json")
    asset = V3Asset(json_filename=sample_ddo_path)
    asset.metadata["main"]["files"][0]["checksum"] = str(uuid.uuid4())

    token = ocn.create_data_token(
        "DataToken1", "DT1", from_wallet=alice, blob="foo_blob"
    )

    assert ocn.assets.create(
        asset.metadata,
        alice,
        [],
        owner_address=alice.address,
        data_token_address=token.address,
    ), "Asset creation failed when given both a datatoken address and owner address."


def test_create_asset_without_dt_address(publisher_ocean_instance):
    """Tests creation of the asset which has not the data token address."""
    ocn = publisher_ocean_instance
    alice = get_publisher_wallet()

    sample_ddo_path = get_resource_path("ddo", "ddo_sa_sample.json")
    asset = V3Asset(json_filename=sample_ddo_path)
    asset.metadata["main"]["files"][0]["checksum"] = str(uuid.uuid4())

    assert ocn.assets.create(
        asset.metadata, alice, [], data_token_address=None
    ), "Asset creation failed with the specified datatoken address."


def test_pay_for_service_insufficient_balance(publisher_ocean_instance):
    """Tests if balance is lower than the purchased amount."""
    ocn = publisher_ocean_instance
    alice = get_publisher_wallet()

    sample_ddo_path = get_resource_path("ddo", "ddo_sa_sample.json")
    asset = V3Asset(json_filename=sample_ddo_path)
    asset.metadata["main"]["files"][0]["checksum"] = str(uuid.uuid4())

    token = ocn.create_data_token(
        "DataToken1", "DT1", from_wallet=alice, blob="foo_blob"
    )

    with pytest.raises(InsufficientBalance):
        ocn.assets.pay_for_service(
            ocn.web3,
            10000000000000,
            token.address,
            asset.did,
            0,
            ZERO_ADDRESS,
            alice,
            alice.address,
        )
