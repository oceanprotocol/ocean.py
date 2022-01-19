#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from ocean_lib.models.dispenser import Dispenser
from ocean_lib.models.models_structures import DispenserData
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.currency import to_wei
from tests.resources.helper_functions import deploy_erc721_erc20, get_address_of_type
from web3 import exceptions


def test_properties(web3, config):
    """Tests the events' properties."""
    dispenser_address = get_address_of_type(config, Dispenser.CONTRACT_NAME)
    dispenser = Dispenser(web3, dispenser_address)

    assert (
        dispenser.event_TokensDispensed.abi["name"] == Dispenser.EVENT_TOKENS_DISPENSED
    )
    assert (
        dispenser.event_OwnerWithdrawed.abi["name"] == Dispenser.EVENT_OWNER_WITHDRAWED
    )
    assert (
        dispenser.event_DispenserAllowedSwapperChanged.abi["name"]
        == Dispenser.EVENT_ALLOWED_SWAPPER_CHANGED
    )
    assert (
        dispenser.event_DispenserDeactivated.abi["name"]
        == Dispenser.EVENT_DISPENSER_DEACTIVATED
    )
    assert (
        dispenser.event_DispenserActivated.abi["name"]
        == Dispenser.EVENT_DISPENSER_ACTIVATED
    )
    assert (
        dispenser.event_DispenserCreated.abi["name"]
        == Dispenser.EVENT_DISPENSER_CREATED
    )


def test_main(web3, config, publisher_wallet, consumer_wallet, factory_deployer_wallet):
    """Tests the main flow of the Dispenser."""

    # get the dispenser
    dispenser = Dispenser(web3, get_address_of_type(config, "Dispenser"))

    _, erc20_token = deploy_erc721_erc20(
        web3, config, publisher_wallet, publisher_wallet, cap=to_wei(50)
    )

    # Tests publisher creates a dispenser with minter role
    dispenser_data = DispenserData(
        dispenser_address=dispenser.address,
        max_balance=to_wei(1),
        max_tokens=to_wei(1),
        allowed_swapper=ZERO_ADDRESS,
    )
    tx = erc20_token.create_dispenser(
        dispenser_data=dispenser_data, with_mint=True, from_wallet=publisher_wallet
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    assert tx_receipt.status == 1

    # Tests publisher gets the dispenser status

    dispenser_status = dispenser.status(erc20_token.address)
    assert dispenser_status[0] is True
    assert dispenser_status[1] == publisher_wallet.address
    assert dispenser_status[2] is True

    # Tests consumer requests more datatokens then allowed transaction reverts
    with pytest.raises(exceptions.ContractLogicError) as err:
        dispenser.dispense(
            data_token=erc20_token.address,
            amount=to_wei(20),
            destination=consumer_wallet.address,
            from_wallet=consumer_wallet,
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert Amount too high"
    )

    # Tests consumer requests data tokens
    tx = dispenser.dispense(
        data_token=erc20_token.address,
        amount=to_wei(1),
        destination=consumer_wallet.address,
        from_wallet=consumer_wallet,
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    assert tx_receipt.status == 1

    # Tests consumer requests more datatokens then exceeds maxBalance
    with pytest.raises(exceptions.ContractLogicError) as err:
        dispenser.dispense(
            data_token=erc20_token.address,
            amount=to_wei(1),
            destination=consumer_wallet.address,
            from_wallet=consumer_wallet,
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert Caller balance too high"
    )

    # Tests publisher deactivates the dispenser
    dispenser.deactivate(from_wallet=publisher_wallet, data_token=erc20_token.address)
    status = dispenser.status(erc20_token.address)
    assert status[0] is False

    # Tests factory deployer should fail to get data tokens
    with pytest.raises(exceptions.ContractLogicError) as err:
        dispenser.dispense(
            data_token=erc20_token.address,
            amount=to_wei("0.00001"),
            destination=factory_deployer_wallet.address,
            from_wallet=factory_deployer_wallet,
        )

    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert Dispenser not active"
    )

    # Tests consumer should fail to activate a dispenser for a token for he is not a minter
    with pytest.raises(exceptions.ContractLogicError) as err:
        dispenser.activate(
            data_token=erc20_token.address,
            max_tokens=to_wei(1),
            max_balance=to_wei(1),
            from_wallet=consumer_wallet,
        )

    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert Invalid owner"
    )

    # Tests publisher creates a dispenser without minter role

    _, erc20_token = deploy_erc721_erc20(
        web3, config, publisher_wallet, publisher_wallet, cap=to_wei(50)
    )

    dispenser_data = DispenserData(
        dispenser_address=dispenser.address,
        max_balance=to_wei(1),
        max_tokens=to_wei(1),
        allowed_swapper=ZERO_ADDRESS,
    )

    erc20_token.create_dispenser(
        from_wallet=publisher_wallet, dispenser_data=dispenser_data, with_mint=False
    )

    # Tests consumer requests data tokens but they are not minted
    with pytest.raises(exceptions.ContractLogicError) as err:
        dispenser.dispense(
            data_token=erc20_token.address,
            amount=to_wei(1),
            destination=consumer_wallet.address,
            from_wallet=consumer_wallet,
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert Not enough reserves"
    )

    # Tests publisher mints tokens and transfer them to the dispenser.

    erc20_token.mint(
        from_wallet=publisher_wallet,
        account_address=dispenser.address,
        value=to_wei(1),
    )

    # Tests consumer requests data tokens
    dispenser.dispense(
        data_token=erc20_token.address,
        amount=to_wei(1),
        destination=consumer_wallet.address,
        from_wallet=consumer_wallet,
    )

    # Tests consumer tries to withdraw all datatokens
    with pytest.raises(exceptions.ContractLogicError) as err:
        dispenser.owner_withdraw(
            data_token=erc20_token.address, from_wallet=consumer_wallet
        )

    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert Invalid owner"
    )

    # Tests publisher withdraws all datatokens
    dispenser.owner_withdraw(
        data_token=erc20_token.address, from_wallet=publisher_wallet
    )

    status = dispenser.status(erc20_token.address)
    assert status[5] == 0
