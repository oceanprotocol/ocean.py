#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json
import os
import time

import pytest
from ocean_lib.models.data_token import DataToken
from ocean_lib.ocean.util import from_base_18, to_base_18
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_utils.ddo.ddo import DDO
from tests.resources.ddo_helpers import get_resource_path


def test_ERC20(alice_ocean, alice_wallet, alice_address, bob_wallet, bob_address):
    """Tests DataToken minting, allowance and transfer."""
    token = alice_ocean.create_data_token(
        "DataToken1", "DT1", from_wallet=alice_wallet, blob="foo_blob"
    )

    assert token.symbol()[:2] == "DT"
    assert token.decimals() == 18
    assert token.balanceOf(alice_address) == 0

    token.mint(alice_address, to_base_18(100.0), from_wallet=alice_wallet)
    assert from_base_18(token.balanceOf(alice_address)) == 100.0

    assert token.allowance(alice_address, bob_address) == 0
    token.approve(bob_address, to_base_18(1.0), from_wallet=alice_wallet)
    assert token.allowance(alice_address, bob_address) == int(1e18)

    token.transfer(bob_address, to_base_18(5.0), from_wallet=alice_wallet)
    assert from_base_18(token.balanceOf(alice_address)) == 95.0
    assert from_base_18(token.balanceOf(bob_address)) == 5.0

    token.transfer(alice_address, to_base_18(3.0), from_wallet=bob_wallet)
    assert from_base_18(token.balanceOf(alice_address)) == 98.0
    assert from_base_18(token.balanceOf(bob_address)) == 2.0

    # assert transfers were successful
    block = alice_ocean.web3.eth.blockNumber
    all_transfers = token.get_all_transfers_from_events(block - 1, block + 1, chunk=1)
    assert len(all_transfers[0]) == 2


def test_status_functions(alice_ocean, alice_wallet, alice_address):
    """Tests various status functions of the DataToken class."""
    token = alice_ocean.create_data_token(
        "DataToken1", "DT1", from_wallet=alice_wallet, blob="foo_blob"
    )

    token.mint(alice_address, to_base_18(100.0), from_wallet=alice_wallet)

    assert from_base_18(token.balanceOf(alice_address)) == 100.0
    assert token.totalSupply() == 100_000_000_000_000_000_000
    assert token.cap() == 1_000_000_000_000_000_000_000
    assert token.datatoken_name() == "DataToken1"
    with pytest.raises(ValueError):
        token.get_event_signature("not a registered event")


def test_blob(alice_ocean, alice_wallet):
    """Tests DataToken creation with a string blob."""
    token = alice_ocean.create_data_token(
        "DataToken1", "DT1", alice_wallet, blob="foo_bar"
    )
    assert token.blob() == "foo_bar"
    assert token.get_simple_url() is None


def test_blob_json(alice_ocean, alice_wallet):
    """Tests DataToken creation with a json blob."""
    blob_dict = {"t": 0, "url": "http://tblob/", "foo": "bar"}
    token = alice_ocean.create_data_token(
        "DataToken1", "DT1", alice_wallet, blob=json.dumps(blob_dict)
    )
    assert token.blob() == json.dumps(blob_dict)
    assert token.get_simple_url() == "http://tblob/"

    blob_dict = {"t": 1, "url": "http://tblob/", "foo": "bar"}
    token = alice_ocean.create_data_token(
        "DataToken1", "DT1", alice_wallet, blob=json.dumps(blob_dict)
    )
    assert token.get_metadata_url() == "http://tblob/"


def test_static_methods():
    """Tests static methods from DataToken class."""
    assert DataToken.get_max_fee_percentage() == 0.002
    assert DataToken.calculate_max_fee(1000) == 2


def test_setMinter(alice_ocean, alice_wallet, alice_address, bob_wallet, bob_address):
    """Tests that a minter can be assigned for a Datatoken."""
    ocean = alice_ocean
    token = ocean.create_data_token(
        "DataToken1", "DT1", from_wallet=alice_wallet, blob="foo_blob"
    )

    # alice is the minter
    token.mint(alice_address, to_base_18(10.0), from_wallet=alice_wallet)
    token.mint(bob_address, to_base_18(10.0), from_wallet=alice_wallet)
    with pytest.raises(Exception):
        token.mint(alice_address, to_base_18(10.0), from_wallet=bob_wallet)

    # switch minter to bob
    token.proposeMinter(bob_address, from_wallet=alice_wallet)
    time.sleep(5)
    token.approveMinter(from_wallet=bob_wallet)
    token.mint(alice_address, to_base_18(10.0), from_wallet=bob_wallet)
    with pytest.raises(Exception):
        token.mint(alice_address, to_base_18(10.0), from_wallet=alice_wallet)
    with pytest.raises(Exception):
        token.mint(bob_address, to_base_18(10.0), from_wallet=alice_wallet)

    # switch minter back to alice
    token.proposeMinter(alice_address, from_wallet=bob_wallet)
    time.sleep(5)
    token.approveMinter(from_wallet=alice_wallet)
    token.mint(alice_address, to_base_18(10.0), from_wallet=alice_wallet)
    with pytest.raises(Exception):
        token.mint(alice_address, to_base_18(10.0), from_wallet=bob_wallet)


def test_transfer_event(
    alice_ocean, alice_wallet, alice_address, bob_wallet, bob_address
):
    """Tests that a transfer event is registered."""
    token = alice_ocean.create_data_token(
        "DataToken1", "DT1", from_wallet=alice_wallet, blob="foo_blob"
    )

    block = alice_ocean.web3.eth.blockNumber
    transfer_event = token.get_transfer_event(block, alice_address, bob_address)
    # different way of retrieving
    transfer_events = token.get_event_logs("Transfer", None, block, block)
    assert transfer_events == []

    token.mint(alice_address, to_base_18(100.0), from_wallet=alice_wallet)
    token.approve(bob_address, to_base_18(1.0), from_wallet=alice_wallet)
    token.transfer(bob_address, to_base_18(5.0), from_wallet=alice_wallet)

    block = alice_ocean.web3.eth.blockNumber
    transfer_event = token.get_transfer_event(block, alice_address, bob_address)
    assert transfer_event["args"]["from"] == alice_address
    assert transfer_event["args"]["to"] == bob_address

    # same transfer event, different way of retrieving
    transfer_event = token.get_event_logs("Transfer", None, block, block)[0]
    assert transfer_event["args"]["from"] == alice_address
    assert transfer_event["args"]["to"] == bob_address


def test_verify_transfer_tx(alice_address, bob_address, alice_ocean, alice_wallet):
    """Tests verify_transfer_tx function."""
    token = alice_ocean.create_data_token(
        "DataToken1", "DT1", from_wallet=alice_wallet, blob="foo_blob"
    )

    with pytest.raises(AssertionError):
        # dummy tx id
        token.verify_transfer_tx("0x0", alice_address, bob_address)

    # an actual transfer does happen
    token.mint(alice_address, to_base_18(100.0), from_wallet=alice_wallet)
    token.approve(bob_address, to_base_18(1.0), from_wallet=alice_wallet)
    tx_id = token.transfer(bob_address, to_base_18(5.0), from_wallet=alice_wallet)

    assert len(token.verify_transfer_tx(tx_id, alice_address, bob_address)) == 2

    with pytest.raises(AssertionError):
        token.verify_transfer_tx(tx_id, "0x0", bob_address)


def test_verify_order_tx(alice_address, bob_address, alice_ocean, alice_wallet):
    """Tests verify_order_tx function."""
    alice_w3 = alice_ocean.web3.eth.blockNumber

    token = alice_ocean.create_data_token(
        "DataToken1", "DT1", from_wallet=alice_wallet, blob="foo_blob"
    )

    token.mint(alice_address, to_base_18(100.0), from_wallet=alice_wallet)
    token.approve(bob_address, to_base_18(1.0), from_wallet=alice_wallet)
    transfer_tx_id = token.transfer(
        bob_address, to_base_18(5.0), from_wallet=alice_wallet
    )

    with pytest.raises(AssertionError):
        # dummy tx id
        token.verify_order_tx(
            alice_w3, "0x0", "some_did", "some_index", "some_amount", alice_address
        )

    transfer_tx_id = token.transfer(
        bob_address, to_base_18(5.0), from_wallet=alice_wallet
    )
    with pytest.raises(AssertionError):
        # tx id is from transfer, not order
        token.verify_order_tx(
            alice_w3,
            transfer_tx_id,
            "some_did",
            "some_index",
            "some_amount",
            alice_address,
        )

    sample_ddo_path = get_resource_path("ddo", "ddo_sa_sample.json")
    asset = DDO(json_filename=sample_ddo_path)
    order_tx_id = token.startOrder(
        alice_address, to_base_18(1.0), 1, ZERO_ADDRESS, alice_wallet
    )

    with pytest.raises(AssertionError):
        # the wrong asset did, this is a sample
        token.verify_order_tx(
            alice_w3, order_tx_id, asset.did, "some_index", "some_amount", alice_address
        )


def test_download(alice_ocean, alice_wallet, tmpdir):
    token = alice_ocean.create_data_token(
        "DataToken1",
        "DT1",
        from_wallet=alice_wallet,
        blob="https://s3.amazonaws.com/testfiles.oceanprotocol.com/info.0.json",
    )

    written_path = token.download(alice_wallet, "test", tmpdir)
    assert os.path.exists(written_path)
