#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest

from ocean_lib.models.dispenser import Dispenser
from ocean_lib.ocean.util import get_address_of_type
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.currency import to_wei


@pytest.mark.unit
def test_main(
    config,
    publisher_wallet,
    consumer_wallet,
    factory_deployer_wallet,
    datatoken,
):
    """Tests the main flow of the Dispenser."""

    # get the dispenser
    dispenser = Dispenser(config, get_address_of_type(config, "Dispenser"))

    # Tests publisher creates a dispenser with minter role
    _ = datatoken.createDispenser(
        dispenser.address,
        to_wei("1"),
        to_wei("1"),
        True,
        ZERO_ADDRESS,
        {"from": publisher_wallet},
    )

    # Tests publisher gets the dispenser status

    dispenser_status = dispenser.status(datatoken.address)
    assert dispenser_status[0] is True
    assert dispenser_status[1] == publisher_wallet.address
    assert dispenser_status[2] is True

    # Tests consumer requests more datatokens then allowed transaction reverts
    with pytest.raises(Exception, match="Amount too high"):
        dispenser.dispense(
            datatoken.address,
            to_wei("20"),
            consumer_wallet.address,
            {"from": consumer_wallet},
        )

    # Tests consumer requests data tokens
    _ = dispenser.dispense(
        datatoken.address,
        to_wei("1"),
        consumer_wallet.address,
        {"from": consumer_wallet},
    )

    # Tests consumer requests more datatokens then exceeds maxBalance
    with pytest.raises(Exception, match="Caller balance too high"):
        dispenser.dispense(
            datatoken.address,
            to_wei("1"),
            consumer_wallet.address,
            {"from": consumer_wallet},
        )

    # Tests publisher deactivates the dispenser
    dispenser.deactivate(datatoken.address, {"from": publisher_wallet})
    status = dispenser.status(datatoken.address)
    assert status[0] is False

    # Tests factory deployer should fail to get data tokens
    with pytest.raises(Exception, match="Dispenser not active"):
        dispenser.dispense(
            datatoken.address,
            to_wei("0.00001"),
            factory_deployer_wallet.address,
            {"from": factory_deployer_wallet},
        )

    # Tests consumer should fail to activate a dispenser for a token for he is not a minter
    with pytest.raises(Exception, match="Invalid owner"):
        dispenser.activate(
            datatoken.address,
            to_wei("1"),
            to_wei("1"),
            {"from": consumer_wallet},
        )


def test_dispenser_creation_without_minter(
    config, publisher_wallet, consumer_wallet, datatoken
):
    """Tests dispenser creation without a minter role."""

    # get the dispenser
    dispenser = Dispenser(config, get_address_of_type(config, "Dispenser"))

    datatoken.createDispenser(
        dispenser.address,
        to_wei("1"),
        to_wei("1"),
        False,
        ZERO_ADDRESS,
        {"from": publisher_wallet},
    )

    # Tests consumer requests data tokens but they are not minted
    with pytest.raises(Exception, match="Not enough reserves"):
        dispenser.dispense(
            datatoken.address,
            to_wei("1"),
            consumer_wallet.address,
            {"from": consumer_wallet},
        )

    # Tests publisher mints tokens and transfer them to the dispenser.
    datatoken.mint(
        dispenser.address,
        to_wei("1"),
        {"from": publisher_wallet},
    )

    # Tests consumer requests data tokens
    dispenser.dispense(
        datatoken.address,
        to_wei("1"),
        consumer_wallet.address,
        {"from": consumer_wallet},
    )

    # Tests publisher withdraws all datatokens
    dispenser.ownerWithdraw(datatoken.address, {"from": publisher_wallet})

    status = dispenser.status(datatoken.address)
    assert status[5] == 0
