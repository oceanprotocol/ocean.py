#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json
import time

import pytest
from ocean_lib.models.data_token import DataToken
from ocean_lib.ocean.util import from_base_18, to_base_18


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
    block = alice_ocean.web3.eth.blockNumber
    token_info = token.get_info(
        alice_ocean.web3,
        from_block=(block - 1),
        to_block=(block + 1),
        include_holders=True,
    )
    assert len(token_info) == 11
    assert token_info["totalSupply"] == 100
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
