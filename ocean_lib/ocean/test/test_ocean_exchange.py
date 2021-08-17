#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import pytest
from ocean_lib.models.fixed_rate_exchange import FixedRateExchange
from ocean_lib.ocean.ocean_exchange import OceanExchange
from ocean_lib.ocean.util import get_contracts_addresses
from ocean_lib.web3_internal.currency import to_wei, wei_and_pretty_ether
from tests.resources.helper_functions import get_consumer_wallet, get_publisher_wallet

_NETWORK = "ganache"


def _get_exchange_address(config):
    """Helper function to retrieve a known exchange address."""
    return get_contracts_addresses(config.address_file, _NETWORK)[
        FixedRateExchange.CONTRACT_NAME
    ]


def test_ocean_exchange(publisher_ocean_instance):
    """Tests various flows of DataToken exchanges."""
    ocn = publisher_ocean_instance
    alice_wallet = get_publisher_wallet()
    bob_wallet = get_consumer_wallet()
    dt = ocn.create_data_token(
        "DataToken1", "DT1", alice_wallet, blob="http://example.com"
    )
    dt.mint(bob_wallet.address, to_wei(100), alice_wallet)
    ox = OceanExchange(
        ocn.web3,
        ocn.OCEAN_address,
        _get_exchange_address(publisher_ocean_instance.config),
        ocn.config,
    )
    rate_in_wei = to_wei("0.9")
    x_id = ox.create(dt.address, rate_in_wei, bob_wallet)
    dt.approve(ox._exchange_address, to_wei(20), bob_wallet)

    # create with invalid token address
    with pytest.raises(ValueError):
        ox.create(ox.ocean_address, rate_in_wei, bob_wallet)

    # TODO: Enable this ValueError handling when the ERC20 check is added in FixedRateExchange.create solidity function
    # with pytest.raises(ValueError):
    # ox.create(ox._exchange_address, 0.9, bob_wallet)

    # create with negative rate, should fail
    with pytest.raises(AssertionError):
        _ = ox.create(dt.address, -rate_in_wei, bob_wallet)

    # create using 0 rate
    with pytest.raises(AssertionError):
        _ = ox.create(dt.address, 0, bob_wallet)

    ##############
    # get_quote
    base_token_amount = ox.get_quote(to_wei(2), exchange_id=x_id)
    expected_base_token_amount = to_wei("1.8")  # 2 * 9
    assert (
        base_token_amount == expected_base_token_amount
    ), f"unexpected quote of {wei_and_pretty_ether(base_token_amount, 'OCEAN')} base tokens, should be {wei_and_pretty_ether(expected_base_token_amount, 'OCEAN')}."

    #############
    # test buying datatokens
    # Alice is buying from exchange owned by bob
    assert (
        ox.buy_at_fixed_rate(
            to_wei(2),
            alice_wallet,
            max_OCEAN_amount=base_token_amount,
            data_token=dt.address,
            exchange_owner=bob_wallet.address,
        )
        is True
    ), "buy datatokens failed"
    assert (
        ox.buy_at_fixed_rate(
            to_wei(2),
            alice_wallet,
            max_OCEAN_amount=base_token_amount,
            exchange_id=x_id,
        )
        is True
    ), "buy datatokens failed"

    rate_in_wei = to_wei("1.0")
    assert ox.setRate(rate_in_wei, bob_wallet, exchange_id=x_id)
    # re-evaluate with new rate
    base_token_amount = ox.get_quote(to_wei(2), exchange_id=x_id)
    expected_base_token_amount = to_wei(2)
    assert (
        base_token_amount == expected_base_token_amount
    ), f"unexpected quote of {wei_and_pretty_ether(base_token_amount, 'OCEAN')} base tokens, should be {wei_and_pretty_ether(expected_base_token_amount, 'OCEAN')}."
