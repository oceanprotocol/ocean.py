#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import lzma
import uuid

from eth_utils import add_0x_prefix, remove_0x_prefix
from ocean_lib.assets.asset import Asset
from ocean_lib.config_provider import ConfigProvider
from ocean_lib.models.data_token import DataToken
from ocean_lib.models.dtfactory import DTFactory
from ocean_lib.models.metadata import MetadataContract
from ocean_lib.ocean.util import get_contracts_addresses
from ocean_lib.web3_internal.web3_provider import Web3Provider
from ocean_utils.ddo.ddo import DDO
from ocean_utils.utils.utilities import checksum
from tests.resources.ddo_helpers import get_resource_path
from tests.resources.helper_functions import get_consumer_wallet, get_publisher_wallet


def get_ddo_sample(datatoken_address):
    """Helper function to get a sample ddo for testing."""
    did = f"did:op:{remove_0x_prefix(datatoken_address)}"
    sample_ddo_path = get_resource_path("ddo", "ddo_sa_sample.json")
    assert sample_ddo_path.exists(), "{} does not exist!".format(sample_ddo_path)

    asset = DDO(json_filename=sample_ddo_path)
    asset.metadata["main"]["files"][0]["checksum"] = str(uuid.uuid4())

    checksum_dict = dict()
    for service in asset.services:
        checksum_dict[str(service.index)] = checksum(service.main)

    asset.add_proof(checksum_dict, get_publisher_wallet())
    asset._did = did
    return asset


def test_ddo_on_chain():
    """Tests chain operations on a DDO."""
    config = ConfigProvider.get_config()
    ddo_address = get_contracts_addresses("ganache", config)[
        MetadataContract.CONTRACT_NAME
    ]
    dtfactory_address = get_contracts_addresses("ganache", config)[
        DTFactory.CONTRACT_NAME
    ]
    ddo_registry = MetadataContract(ddo_address)
    wallet = get_publisher_wallet()
    web3 = Web3Provider.get_web3()

    dtfactory = DTFactory(dtfactory_address)
    tx_id = dtfactory.createToken("", "dt1", "dt1", 1000, wallet)
    dt = DataToken(dtfactory.get_token_address(tx_id))

    # test create ddo
    asset = get_ddo_sample(dt.address)
    old_name = asset.metadata["main"]["name"]
    txid = ddo_registry.create(
        asset.asset_id, b"", lzma.compress(web3.toBytes(text=asset.as_text())), wallet
    )
    assert ddo_registry.verify_tx(txid), f"create ddo failed: txid={txid}"
    logs = ddo_registry.event_MetadataCreated.processReceipt(
        ddo_registry.get_tx_receipt(txid)
    )
    assert logs, f"no logs found for create ddo tx {txid}"
    log = logs[0]
    assert add_0x_prefix(log.args.dataToken) == asset.asset_id
    # read back the asset ddo from the event log
    ddo_text = web3.toText(lzma.decompress(log.args.data))
    assert ddo_text == asset.as_text(), "ddo text does not match original."

    _asset = Asset(json_text=ddo_text)
    assert _asset.did == asset.did, "did does not match."
    name = _asset.metadata["main"]["name"]
    assert name == old_name, f"name does not match: {name} != {old_name}"

    # test_update ddo
    asset.metadata["main"]["name"] = "updated name for test"
    txid = ddo_registry.update(
        asset.asset_id, b"", lzma.compress(web3.toBytes(text=asset.as_text())), wallet
    )
    assert ddo_registry.verify_tx(txid), f"update ddo failed: txid={txid}"
    logs = ddo_registry.event_MetadataUpdated.processReceipt(
        ddo_registry.get_tx_receipt(txid)
    )
    assert logs, f"no logs found for update ddo tx {txid}"
    log = logs[0]
    assert add_0x_prefix(log.args.dataToken) == asset.asset_id
    # read back the asset ddo from the event log
    ddo_text = web3.toText(lzma.decompress(log.args.data))
    assert ddo_text == asset.as_text(), "ddo text does not match original."
    _asset = Asset(json_text=ddo_text)
    assert (
        _asset.metadata["main"]["name"] == "updated name for test"
    ), "name does not seem to be updated."
    assert DataToken(asset.asset_id).contract_concise.isMinter(wallet.address)

    # test update fails from wallet other than the original publisher
    bob = get_consumer_wallet()
    try:
        txid = ddo_registry.update(
            asset.asset_id, b"", lzma.compress(web3.toBytes(text=asset.as_text())), bob
        )
        assert ddo_registry.verify_tx(txid) is False, f"update ddo failed: txid={txid}"
        logs = ddo_registry.event_MetadataUpdated.processReceipt(
            ddo_registry.get_tx_receipt(txid)
        )
        assert (
            not logs
        ), f"should be no logs for MetadataUpdated, but seems there are some logs: tx {txid}, logs {logs}"
    except ValueError:
        print("as expected, only owner can update a published ddo.")

    # test ddoOwner
    assert DataToken(asset.asset_id).contract_concise.isMinter(wallet.address), (
        f"ddo owner does not match the expected publisher address {wallet.address}, "
        f"owner is {DataToken(asset.asset_id).contract_concise.minter(wallet.address)}"
    )
