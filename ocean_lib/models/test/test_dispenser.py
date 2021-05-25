#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import pytest
from ocean_lib.models.dispenser import DispenserContract


def test_dispenser_activation(
    contracts_addresses, alice_ocean, alice_wallet, bob_wallet
):
    dispenser_address = contracts_addresses["Dispenser"]
    contract = DispenserContract(dispenser_address)
    token = alice_ocean.create_data_token(
        "DataToken1", "DT1", from_wallet=alice_wallet, blob="foo_blob"
    )
    res = contract.status_dict(token.address)
    assert res["active"] is False
    assert res["owner"] is None
    assert res["minterApproved"] is False
    assert res["isTrueMinter"] is False
    assert res["maxTokens"] == 0
    assert res["maxBalance"] == 0
    assert res["balance"] == 0

    contract.activate(token.address, 100, 100, alice_wallet)
    res = contract.status_dict(token.address)
    assert res["active"]
    assert res["owner"] == alice_wallet.address

    with pytest.raises(ValueError):
        contract.deactivate(token.address, bob_wallet)
    contract.deactivate(token.address, alice_wallet)


def test_dispenser_minting(contracts_addresses, alice_ocean, alice_wallet, bob_wallet):
    dispenser_address = contracts_addresses["Dispenser"]
    dispenser = DispenserContract(dispenser_address)
    token = alice_ocean.create_data_token(
        "DataToken1", "DT1", from_wallet=alice_wallet, blob="foo_blob"
    )
    dispenser.activate(token.address, 1000, 1000, alice_wallet)

    dispenser.make_minter(token.address, alice_wallet)
    res = dispenser.status_dict(token.address)
    assert res["minterApproved"]
    dispenser.dispense(token.address, 1, alice_wallet)
    dispenser.dispense(token.address, 1, bob_wallet)

    dispenser.cancel_minter(token.address, alice_wallet)
    dispenser.owner_withdraw(token.address, alice_wallet)
    with pytest.raises(ValueError):
        dispenser.dispense(token.address, 1, alice_wallet)
