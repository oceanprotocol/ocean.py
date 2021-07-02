#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import pytest
from ocean_lib.models.dispenser import DispenserContract


def test_dispenser_status(contracts_addresses, alice_ocean, alice_wallet, bob_wallet):
    dispenser_address = contracts_addresses["Dispenser"]
    dispenser = DispenserContract(alice_ocean.web3, dispenser_address)
    token = alice_ocean.create_data_token(
        "DataToken1", "DT1", from_wallet=alice_wallet, blob="foo_blob"
    )
    assert dispenser.is_active(token.address) is False
    assert (
        dispenser.owner(token.address) == "0x0000000000000000000000000000000000000000"
    )
    assert dispenser.is_minter_approved(token.address) is False
    assert dispenser.is_true_minter(token.address) is False
    assert dispenser.max_tokens(token.address) == 0
    assert dispenser.max_balance(token.address) == 0
    assert dispenser.balance(token.address) == 0


def test_dispenser_activation(
    contracts_addresses, alice_ocean, alice_wallet, bob_wallet
):
    dispenser_address = contracts_addresses["Dispenser"]
    dispenser = DispenserContract(alice_ocean.web3, dispenser_address)
    token = alice_ocean.create_data_token(
        "DataToken1", "DT1", from_wallet=alice_wallet, blob="foo_blob"
    )

    dispenser.activate(token.address, 100, 100, alice_wallet)
    assert dispenser.is_active(token.address)
    assert dispenser.owner(token.address) == alice_wallet.address

    with pytest.raises(ValueError):
        # try to deactivate a different wallet
        dispenser.deactivate(token.address, bob_wallet)

    assert dispenser.deactivate(token.address, alice_wallet)


def test_dispenser_minting(contracts_addresses, alice_ocean, alice_wallet, bob_wallet):
    dispenser_address = contracts_addresses["Dispenser"]
    dispenser = DispenserContract(alice_ocean.web3, dispenser_address)
    token = alice_ocean.create_data_token(
        "DataToken1", "DT1", from_wallet=alice_wallet, blob="foo_blob"
    )

    # not yet activated
    assert dispenser.is_dispensable(token.address, 1, alice_wallet) is False
    with pytest.raises(ValueError):
        dispenser.dispense(token.address, 1, alice_wallet)

    dispenser.activate(token.address, 1000, 1000, alice_wallet)

    dispenser.make_minter(token.address, alice_wallet)
    assert dispenser.is_minter_approved(token.address)
    assert dispenser.is_dispensable(token.address, 1, alice_wallet)
    dispenser.dispense(token.address, 1, alice_wallet)
    assert dispenser.is_dispensable(token.address, 1, bob_wallet)
    dispenser.dispense(token.address, 1, bob_wallet)

    # can not dispense 0
    assert dispenser.is_dispensable(token.address, 0, alice_wallet) is False
    with pytest.raises(ValueError):
        dispenser.dispense(token.address, 0, alice_wallet)

    dispenser.cancel_minter(token.address, alice_wallet)
    dispenser.owner_withdraw(token.address, alice_wallet)

    # no balance left
    assert dispenser.is_dispensable(token.address, 1, alice_wallet) is False
    with pytest.raises(ValueError):
        dispenser.dispense(token.address, 1, alice_wallet)
