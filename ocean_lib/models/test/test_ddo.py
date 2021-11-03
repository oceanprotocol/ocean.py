#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import lzma
import uuid

import pytest
from eth_utils import add_0x_prefix, remove_0x_prefix
from ocean_lib.assets.asset import V3Asset
from ocean_lib.assets.credentials import AddressCredential
from ocean_lib.common.agreements.consumable import ConsumableCodes, MalformedCredential
from ocean_lib.models.data_token import DataToken
from ocean_lib.models.dtfactory import DTFactory
from ocean_lib.models.metadata import MetadataContract
from ocean_lib.ocean.util import get_contracts_addresses
from ocean_lib.utils.utilities import checksum
from tests.resources.ddo_helpers import get_resource_path
from tests.resources.helper_functions import get_consumer_wallet, get_publisher_wallet
from web3.logs import DISCARD
from web3.main import Web3


def get_ddo_sample(datatoken_address):
    """Helper function to get a sample ddo for testing."""
    did = f"did:op:{remove_0x_prefix(datatoken_address)}"
    sample_ddo_path = get_resource_path("ddo", "ddo_sa_sample.json")
    assert sample_ddo_path.exists(), "{} does not exist!".format(sample_ddo_path)

    asset = V3Asset(json_filename=sample_ddo_path)
    asset.metadata["main"]["files"][0]["checksum"] = str(uuid.uuid4())

    checksum_dict = dict()
    for service in asset.services:
        checksum_dict[str(service.index)] = checksum(service.main)

    asset.add_proof(checksum_dict, get_publisher_wallet())
    asset.did = did
    return asset


def test_ddo_credentials_addresses_both():
    """Tests DDO credentials when both deny and allow lists exist on the asset."""
    sample_ddo_path = get_resource_path("ddo", "ddo_sa_sample_with_credentials.json")
    assert sample_ddo_path.exists(), "{} does not exist!".format(sample_ddo_path)

    ddo = V3Asset(json_filename=sample_ddo_path)
    address_credential = AddressCredential(ddo)
    assert address_credential.get_addresses_of_class("allow") == ["0x123", "0x456a"]
    assert address_credential.get_addresses_of_class("deny") == ["0x2222", "0x333"]
    assert (
        address_credential.validate_access({"type": "address", "value": "0x111"})
        == ConsumableCodes.CREDENTIAL_NOT_IN_ALLOW_LIST
    )
    assert (
        address_credential.validate_access({"type": "address", "value": "0x456A"})
        == ConsumableCodes.OK
    )
    # if "allow" exists, "deny" is not checked anymore


def test_ddo_credentials_addresses_only_deny():
    """Tests DDO credentials when only the deny list exists on the asset."""
    sample_ddo_path = get_resource_path("ddo", "ddo_sa_sample_with_credentials.json")
    assert sample_ddo_path.exists(), "{} does not exist!".format(sample_ddo_path)
    # remove allow to test the behaviour of deny
    ddo = V3Asset(json_filename=sample_ddo_path)
    ddo.credentials.pop("allow")

    address_credential = AddressCredential(ddo)
    assert address_credential.get_addresses_of_class("allow") == []
    assert address_credential.get_addresses_of_class("deny") == ["0x2222", "0x333"]
    assert (
        address_credential.validate_access({"type": "address", "value": "0x111"})
        == ConsumableCodes.OK
    )
    assert (
        address_credential.validate_access({"type": "address", "value": "0x333"})
        == ConsumableCodes.CREDENTIAL_IN_DENY_LIST
    )

    credential = {"type": "address", "value": ""}
    with pytest.raises(MalformedCredential):
        address_credential.validate_access(credential)


def test_ddo_credentials_addresses_no_access_list():
    """Tests DDO credentials when neither deny, nor allow lists exist on the asset."""
    sample_ddo_path = get_resource_path("ddo", "ddo_sa_sample_with_credentials.json")
    assert sample_ddo_path.exists(), "{} does not exist!".format(sample_ddo_path)

    # if "allow" OR "deny" exist, we need a credential,
    # so remove both to test the behaviour of no credential supplied
    ddo = V3Asset(json_filename=sample_ddo_path)
    address_credential = AddressCredential(ddo)
    ddo.credentials.pop("allow")
    ddo.credentials.pop("deny")

    assert address_credential.validate_access() == ConsumableCodes.OK

    # test that we can use another credential if address is not required
    assert (
        ddo.is_consumable(
            {"type": "somethingelse", "value": "test"}, with_connectivity_check=False
        )
        == ConsumableCodes.OK
    )


def test_ddo_connection(config):
    ddo = V3Asset("did:op:testdid")
    provider_uri = config.provider_url
    assert (
        ddo.is_consumable(with_connectivity_check=True, provider_uri=provider_uri)
        == ConsumableCodes.CONNECTIVITY_FAIL
    )


def test_ddo_credentials_disabled():
    sample_ddo_path = get_resource_path("ddo", "ddo_sa_sample_disabled.json")
    assert sample_ddo_path.exists(), "{} does not exist!".format(sample_ddo_path)

    ddo = V3Asset(json_filename=sample_ddo_path)
    assert ddo.is_disabled
    assert not ddo.is_enabled

    ddo.enable()
    assert not ddo.is_disabled
    assert ddo.is_enabled

    ddo.disable()
    assert ddo.is_consumable() == ConsumableCodes.ASSET_DISABLED


def test_ddo_on_chain(config, web3):
    """Tests chain operations on a DDO."""
    ddo_address = get_contracts_addresses(config.address_file, "ganache")[
        MetadataContract.CONTRACT_NAME
    ]
    dtfactory_address = get_contracts_addresses(config.address_file, "ganache")[
        DTFactory.CONTRACT_NAME
    ]
    ddo_registry = MetadataContract(web3, ddo_address)
    wallet = get_publisher_wallet()

    dtfactory = DTFactory(web3, dtfactory_address)
    tx_id = dtfactory.createToken("", "dt1", "dt1", 1000, wallet)
    dt = DataToken(web3, dtfactory.get_token_address(tx_id))

    # test create ddo
    asset = get_ddo_sample(dt.address)
    old_name = asset.metadata["main"]["name"]
    txid = ddo_registry.create(
        asset.asset_id, b"", lzma.compress(Web3.toBytes(text=asset.as_text())), wallet
    )
    assert ddo_registry.verify_tx(txid), f"create ddo failed: txid={txid}"
    logs = ddo_registry.event_MetadataCreated.processReceipt(
        ddo_registry.get_tx_receipt(web3, txid), errors=DISCARD
    )
    assert logs, f"no logs found for create ddo tx {txid}"
    log = logs[0]
    assert add_0x_prefix(log.args.dataToken) == asset.asset_id
    # read back the asset ddo from the event log
    ddo_text = Web3.toText(lzma.decompress(log.args.data))
    assert ddo_text == asset.as_text(), "ddo text does not match original."

    _asset = V3Asset(json_text=ddo_text)
    assert _asset.did == asset.did, "did does not match."
    name = _asset.metadata["main"]["name"]
    assert name == old_name, f"name does not match: {name} != {old_name}"

    # test_update ddo
    asset.metadata["main"]["name"] = "updated name for test"
    txid = ddo_registry.update(
        asset.asset_id, b"", lzma.compress(Web3.toBytes(text=asset.as_text())), wallet
    )
    assert ddo_registry.verify_tx(txid), f"update ddo failed: txid={txid}"
    logs = ddo_registry.event_MetadataUpdated.processReceipt(
        ddo_registry.get_tx_receipt(web3, txid), errors=DISCARD
    )
    assert logs, f"no logs found for update ddo tx {txid}"
    log = logs[0]
    assert add_0x_prefix(log.args.dataToken) == asset.asset_id
    # read back the asset ddo from the event log
    ddo_text = Web3.toText(lzma.decompress(log.args.data))
    assert ddo_text == asset.as_text(), "ddo text does not match original."
    _asset = V3Asset(json_text=ddo_text)
    assert (
        _asset.metadata["main"]["name"] == "updated name for test"
    ), "name does not seem to be updated."
    assert DataToken(web3, asset.asset_id).contract.caller.isMinter(wallet.address)

    # test update fails from wallet other than the original publisher
    bob = get_consumer_wallet()
    try:
        txid = ddo_registry.update(
            asset.asset_id, b"", lzma.compress(Web3.toBytes(text=asset.as_text())), bob
        )
        assert ddo_registry.verify_tx(txid) is False, f"update ddo failed: txid={txid}"
        logs = ddo_registry.event_MetadataUpdated.processReceipt(
            ddo_registry.get_tx_receipt(web3, txid), errors=DISCARD
        )
        assert (
            not logs
        ), f"should be no logs for MetadataUpdated, but seems there are some logs: tx {txid}, logs {logs}"
    except ValueError:
        print("as expected, only owner can update a published ddo.")

    # test ddoOwner
    assert DataToken(web3, asset.asset_id).contract.caller.isMinter(wallet.address), (
        f"ddo owner does not match the expected publisher address {wallet.address}, "
        f"owner is {DataToken(web3, asset.asset_id).contract.caller.minter(wallet.address)}"
    )


def test_ddo_address_utilities():
    sample_ddo_path = get_resource_path("ddo", "ddo_sa_sample_with_credentials.json")
    assert sample_ddo_path.exists(), "{} does not exist!".format(sample_ddo_path)

    ddo = V3Asset(json_filename=sample_ddo_path)

    assert ddo.allowed_addresses == ["0x123", "0x456a"]

    ddo.add_address_to_allow_list("0xAbc12")
    assert ddo.allowed_addresses == ["0x123", "0x456a", "0xabc12"]
    ddo.remove_address_from_allow_list("0xAbc12")
    assert ddo.allowed_addresses == ["0x123", "0x456a"]
    ddo.remove_address_from_allow_list("0x123")
    assert ddo.allowed_addresses == ["0x456a"]
    ddo.remove_address_from_allow_list("0x456a")
    assert ddo.allowed_addresses == []

    assert ddo.denied_addresses == ["0x2222", "0x333"]
    # does not exist
    ddo.remove_address_from_deny_list("0xasfaweg")
    assert ddo.denied_addresses == ["0x2222", "0x333"]
    ddo.add_address_to_deny_list("0xasfaweg")
    assert ddo.denied_addresses == ["0x2222", "0x333", "0xasfaweg"]

    ddo = V3Asset()
    assert ddo.allowed_addresses == []
    ddo.add_address_to_allow_list("0xAbc12")
    assert ddo.allowed_addresses == ["0xabc12"]
    # double adding
    ddo.add_address_to_allow_list("0xAbc12")
    assert ddo.allowed_addresses == ["0xabc12"]


def test_ddo_retiring():
    sample_ddo_path = get_resource_path("ddo", "ddo_sa_sample.json")
    assert sample_ddo_path.exists(), "{} does not exist!".format(sample_ddo_path)

    ddo = V3Asset(json_filename=sample_ddo_path)
    assert not ddo.is_retired

    ddo.retire()
    assert ddo.is_retired
    assert ddo.is_consumable() == ConsumableCodes.ASSET_DISABLED

    ddo.unretire()
    assert not ddo.is_retired


def test_ddo_unlisting():
    sample_ddo_path = get_resource_path("ddo", "ddo_sa_sample.json")
    assert sample_ddo_path.exists(), "{} does not exist!".format(sample_ddo_path)

    ddo = V3Asset(json_filename=sample_ddo_path)
    assert ddo.is_listed

    ddo.unlist()
    assert not ddo.is_listed

    ddo.list()
    assert ddo.is_listed
