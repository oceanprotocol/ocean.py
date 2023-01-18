#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest

from ocean_lib.models.dispenser import Dispenser, DispenserStatus
from ocean_lib.ocean.util import from_wei, get_address_of_type, to_wei
from ocean_lib.web3_internal.constants import MAX_UINT256, ZERO_ADDRESS
from tests.resources.helper_functions import (
    deploy_erc721_erc20,
    delay_transaction,
    confirm_failed
)


@pytest.mark.unit
def test_DispenserStatus():
    """Test DispenserStatus object"""
    # set status_tup
    active = True
    owner = "0x1234"
    is_minter = True
    max_tokens = 456
    max_bal = 789
    bal = 3
    swpr = ZERO_ADDRESS  # allowed swapper. ZERO_ADDRESS = anyone can request

    # create the object
    status_tup = (active, owner, is_minter, max_tokens, max_bal, bal, swpr)
    status = DispenserStatus(status_tup)

    # verify status
    assert isinstance(status, DispenserStatus)
    assert status.active
    assert status.owner_address == "0x1234"
    assert status.is_minter is True
    assert status.max_tokens == 456
    assert status.max_balance == 789
    assert status.balance == 3
    assert status.allowed_swapper == ZERO_ADDRESS

    # verify __str__
    s = str(status)
    assert "DispenserStatus" in s
    assert "active = True" in s
    assert "owner_address = 0x1234" in s
    assert "is_minter" in s
    assert "max_tokens" in s
    assert "max_balance" in s
    assert "balance" in s
    assert "allowed_swapper = anyone" in s


@pytest.mark.unit
def test_main_flow_via_simple_ux_and_good_defaults(
    config,
    publisher_wallet,
    consumer_wallet,
):
    """
    Tests main flow, via simple interface Datatoken.create_dispenser().
    Focus on the basic steps.
    Use good defaults for max_tokens, max_balance, more.
    """
    _, datatoken = deploy_erc721_erc20(config, publisher_wallet, publisher_wallet)

    # basic steps
    datatoken.create_dispenser({"from": publisher_wallet})
    datatoken.dispense("3 ether", {"from": consumer_wallet})

    # check balance
    bal = datatoken.balanceOf(consumer_wallet.address)
    assert from_wei(bal) == 3

    # check status
    status = datatoken.dispenser_status()
    assert isinstance(status, DispenserStatus)
    assert status.active
    assert status.owner_address == publisher_wallet.address
    assert status.is_minter is True
    assert status.max_tokens == MAX_UINT256
    assert status.max_balance == MAX_UINT256
    assert status.balance == 0  # 0, not 3, because it mints on the fly
    assert status.allowed_swapper == ZERO_ADDRESS  # anyone can request


@pytest.mark.unit
def test_main_flow_via_simple_ux_and_setting_token_counts(
    config,
    publisher_wallet,
    consumer_wallet,
):
    """
    Tests main flow, via simple interface Datatoken.create_dispenser().
    Focus on the basic steps.
    Set values for max_tokens, max_balance.
    """
    _, datatoken = deploy_erc721_erc20(config, publisher_wallet, publisher_wallet)
    # set params
    max_tokens = to_wei(456)  # max # tokens to dispense
    max_balance = to_wei(789)  # max balance of requester

    # basic steps
    datatoken.create_dispenser({"from": publisher_wallet}, max_tokens, max_balance)
    datatoken.dispense("3 ether", {"from": consumer_wallet})

    # check status
    status = datatoken.dispenser_status()
    assert from_wei(status.max_tokens) == 456
    assert from_wei(status.max_balance) == 789
    assert status.balance == 0


@pytest.mark.unit
def test_main_flow_via_contract_directly(
    config,
    publisher_wallet,
    consumer_wallet,
    factory_deployer_wallet,
):
    """
    Tests main flow, via direct calls to smart contracts (more args).
    Has not just basic steps, but also advanced actions.
    """
    _, datatoken = deploy_erc721_erc20(config, publisher_wallet, publisher_wallet)

    # get the dispenser
    dispenser = Dispenser(config, get_address_of_type(config, "Dispenser"))

    # Tests publisher creates a dispenser with minter role
    _ = datatoken.create_dispenser(
        {"from": publisher_wallet},
        to_wei(1),
        to_wei(1),
    )

    # Tests publisher gets the dispenser status

    dispenser_status = dispenser.status(datatoken.address)
    assert dispenser_status[0] is True
    assert dispenser_status[1] == publisher_wallet.address
    assert dispenser_status[2] is True

    # Tests consumer requests more datatokens then allowed transaction reverts
    with delay_transaction():
        tx = dispenser.dispense(
            datatoken.address,
            to_wei(20),
            consumer_wallet.address,
            {"from": consumer_wallet, "required_confs": 0},
        )
    confirm_failed(tx, "Amount too high")

    # Tests consumer requests data tokens
    _ = dispenser.dispense(
        datatoken.address,
        to_wei(1),
        consumer_wallet.address,
        {"from": consumer_wallet},
    )

    # Tests consumer requests more datatokens then exceeds maxBalance
    with delay_transaction():
        tx = dispenser.dispense(
            datatoken.address,
            to_wei(1),
            consumer_wallet.address,
            {"from": consumer_wallet, "required_confs": 0},
        )
    confirm_failed(tx, "Caller balance too high")

    # Tests publisher deactivates the dispenser
    dispenser.deactivate(datatoken.address, {"from": publisher_wallet})
    status = dispenser.status(datatoken.address)
    assert status[0] is False

    # Tests factory deployer should fail to get data tokens
    with delay_transaction():
        tx = dispenser.dispense(
            datatoken.address,
            to_wei(0.00001),
            factory_deployer_wallet.address,
            {"from": factory_deployer_wallet, "required_confs": 0},
        )
    confirm_failed(tx, "Dispenser not active")

    # Tests consumer should fail to activate a dispenser for a token for he is not a minter
    with delay_transaction():
        tx = dispenser.activate(
            datatoken.address,
            to_wei(1),
            to_wei(1),
            {"from": consumer_wallet, "required_confs": 0},
        )
    confirm_failed(tx, "Invalid owner")


def test_dispenser_creation_without_minter(config, publisher_wallet, consumer_wallet):
    """Tests dispenser creation without a minter role."""
    _, datatoken = deploy_erc721_erc20(config, publisher_wallet, publisher_wallet)

    # get the dispenser
    dispenser = Dispenser(config, get_address_of_type(config, "Dispenser"))

    datatoken.create_dispenser(
        {"from": publisher_wallet},
        to_wei(1),
        to_wei(1),
        with_mint=False,
    )

    # Tests consumer requests data tokens but they are not minted
    with delay_transaction():
        tx = dispenser.dispense(
            datatoken.address,
            to_wei(1),
            consumer_wallet.address,
            {"from": consumer_wallet, "required_confs": 0},
        )
    confirm_failed(tx, "Not enough reserves")

    # Tests publisher mints tokens and transfer them to the dispenser.
    datatoken.mint(
        dispenser.address,
        to_wei(1),
        {"from": publisher_wallet},
    )

    # Tests consumer requests data tokens
    dispenser.dispense(
        datatoken.address,
        to_wei(1),
        consumer_wallet.address,
        {"from": consumer_wallet},
    )

    # Tests publisher withdraws all datatokens
    dispenser.ownerWithdraw(datatoken.address, {"from": publisher_wallet})

    status = dispenser.status(datatoken.address)
    assert status[5] == 0
