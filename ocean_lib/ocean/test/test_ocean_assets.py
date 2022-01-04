#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import time
import uuid
from unittest.mock import patch

import pytest
from ocean_lib.agreements.file_objects import FilesTypeFactory
from ocean_lib.assets.asset import Asset
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.exceptions import InsufficientBalance
from ocean_lib.models.models_structures import ErcCreateData
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from tests.resources.ddo_helpers import (
    get_resource_path,
    get_sample_ddo,
    wait_for_update,
)
from tests.resources.helper_functions import get_address_of_type


def create_asset(ocean, publisher, config, metadata=None):
    """Helper function for asset creation based on ddo_sa_sample.json."""
    erc20_data = ErcCreateData(
        template_index=1,
        strings=["Datatoken 1", "DT1"],
        addresses=[
            publisher.address,
            publisher.address,
            ZERO_ADDRESS,
            get_address_of_type(config, "Ocean"),
        ],
        uints=[ocean.web3.toWei("0.5", "ether"), 0],
        bytess=[b""],
    )

    if not metadata:
        metadata = {
            "created": "2020-11-15T12:27:48Z",
            "updated": "2021-05-17T21:58:02Z",
            "description": "Sample description",
            "name": "Sample asset",
            "type": "dataset",
            "author": "OPF",
            "license": "https://market.oceanprotocol.com/terms",
        }
    data_provider = DataServiceProvider
    file1_dict = {"type": "url", "url": "https://url.com/file1.csv", "method": "GET"}
    file1 = FilesTypeFactory(file1_dict)
    encrypt_response = data_provider.encrypt(
        [file1], "http://172.15.0.4:8030/api/services/encrypt"
    )
    encrypted_files = encrypt_response.content.decode("utf-8")

    ddo = ocean.assets.create(
        metadata, publisher, encrypted_files, erc20_tokens_data=[erc20_data]
    )

    return ddo


def test_register_asset(publisher_ocean_instance, publisher_wallet, consumer_wallet):
    """Test various paths for asset registration.

    Happy paths are tested in the publish flow."""
    ocn = publisher_ocean_instance

    invalid_did = "did:op:0123456789"
    assert ocn.assets.resolve(invalid_did) is None


@pytest.mark.skip(reason="TODO: update function on OceanAssets class")
def test_update(publisher_ocean_instance, publisher_wallet, consumer_wallet, config):
    ocn = publisher_ocean_instance
    block = ocn.web3.eth.block_number
    alice = publisher_wallet
    bob = consumer_wallet

    ddo = create_asset(ocn, alice, config)

    # Publish the metadata
    _name = "updated name"
    ddo.metadata["name"] = _name
    assert ddo.metadata["name"] == _name, "Asset's name was not updated."

    with pytest.raises(ValueError):
        ocn.assets.update(ddo, bob)

    _ = ocn.assets.update(ddo, alice)
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


def test_ocean_assets_search(publisher_ocean_instance, publisher_wallet, config):
    """Tests that a created asset can be searched successfully."""
    identifier = str(uuid.uuid1()).replace("-", "")
    metadata = {
        "created": "2020-11-15T12:27:48Z",
        "updated": "2021-05-17T21:58:02Z",
        "description": "Sample description",
        "name": identifier,
        "type": "dataset",
        "author": "OPF",
        "license": "https://market.oceanprotocol.com/terms",
    }

    assert (
        len(publisher_ocean_instance.assets.search(identifier)) == 0
    ), "Asset search failed."

    create_asset(publisher_ocean_instance, publisher_wallet, config, metadata)

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
                            "fields": ["metadata.name"],
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
                            "fields": ["metadata.name"],
                        }
                    }
                }
            )
        )
        == 0
    )


def test_ocean_assets_validate(publisher_ocean_instance):
    """Tests that the validate function returns an error for invalid metadata."""
    ddo_dict = get_sample_ddo()
    ddo = Asset.from_dict(ddo_dict)

    assert publisher_ocean_instance.assets.validate(
        ddo
    ), "asset should be valid, unless the schema changed."


def test_ocean_assets_algorithm(publisher_ocean_instance, publisher_wallet, config):
    """Tests the creation of an algorithm DDO."""
    metadata = {
        "created": "2020-11-15T12:27:48Z",
        "updated": "2021-05-17T21:58:02Z",
        "description": "Sample description",
        "name": "Sample algorithm asset",
        "type": "algorithm",
        "author": "OPF",
        "license": "https://market.oceanprotocol.com/terms",
        "algorithm": {
            "language": "scala",
            "format": "docker-image",
            "version": "0.1",
            "container": {
                "entrypoint": "node $ALGO",
                "image": "node",
                "tag": "10",
                "checksum": "test",
            },
        },
    }

    ddo = create_asset(publisher_ocean_instance, publisher_wallet, config, metadata)
    assert ddo, "DDO None. The ddo is not cached after the creation."


@pytest.mark.skip(reason="TODO: download function on OceanAssets class")
def test_download_fails(publisher_ocean_instance, publisher_wallet):
    """Tests failures of assets download function."""
    with patch("ocean_lib.ocean.ocean_assets.OceanAssets.resolve") as mock:
        mock.return_value = get_sample_ddo()
        with pytest.raises(AssertionError):
            publisher_ocean_instance.assets.download(
                "0x1", 1, publisher_wallet, "", "", -4
            )
        with pytest.raises(TypeError):
            publisher_ocean_instance.assets.download(
                "0x1", "", publisher_wallet, "", "", "string_index"
            )


def test_create_bad_metadata(publisher_ocean_instance, publisher_wallet, config):
    """Tests that we can't create the asset with plecos failure."""
    metadata = {
        "created": "2020-11-15T12:27:48Z",
        "updated": "2021-05-17T21:58:02Z",
        "description": "Sample description",
        # name missing intentionally
        "type": "dataset",
        "author": "OPF",
        "license": "https://market.oceanprotocol.com/terms",
    }
    with pytest.raises(AssertionError):
        create_asset(publisher_ocean_instance, publisher_wallet, config, metadata)

    metadata["name"] = "Sample asset"
    metadata.pop("type")
    with pytest.raises(AssertionError):
        create_asset(publisher_ocean_instance, publisher_wallet, config, metadata)


#  TODO: add more creation tests. The old v3 ones did not apply anymore


@pytest.mark.skip(reason="TODO: pay_for_service function on OceanAssets class")
def test_pay_for_service_insufficient_balance(
    publisher_ocean_instance, publisher_wallet
):
    """Tests if balance is lower than the purchased amount."""
    #  FIXME: this test still has v3 structure, please adapt
    ocn = publisher_ocean_instance
    alice = publisher_wallet

    sample_ddo_path = get_resource_path("ddo", "ddo_sa_sample.json")
    asset = Asset(json_filename=sample_ddo_path)
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
