#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import pytest
from ocean_lib.models.fixed_rate_exchange import FixedRateExchange
from ocean_lib.ocean.ocean_exchange import OceanExchange

from ocean_lib.ocean.util import get_contracts_addresses
from ocean_lib.web3_internal.currency import pretty_ether_and_wei, to_wei
from tests.resources.helper_functions import get_consumer_wallet, get_publisher_wallet

_NETWORK = "ganache"


def _get_exchange_address(config):
    """Helper function to retrieve a known exchange address."""
    return get_contracts_addresses(config.address_file, _NETWORK)[
        FixedRateExchange.CONTRACT_NAME
    ]


def test_search_exchange_by_nonexistent_data_token(publisher_ocean_instance):
    """Tests searching exchanges with a nonexistent data token address."""
    ocn = publisher_ocean_instance
    foo_data_token = "0xcd2a3d9f938e13cd947ec05abc7fe734df8dd826"
    with pytest.raises(AssertionError) as err:
        ocn.exchange.search_exchange_by_data_token(foo_data_token)
    assert (
        err.value.args[0]
        == f"No token with '{foo_data_token}' address was created before."
    )


def test_search_exchange_by_data_token(publisher_ocean_instance):
    """Tests searching exchanges which have matching data token address."""
    ocn = publisher_ocean_instance
    alice_wallet = get_publisher_wallet()
    bob_wallet = get_consumer_wallet()
    dt = ocn.create_data_token(
        "DataToken1", "DT1", alice_wallet, blob=ocn.config.metadata_cache_uri
    )
    dt.mint(bob_wallet.address, to_wei(100), alice_wallet)
    dt.approve(ocn.exchange._exchange_address, to_wei(100), alice_wallet)

    exchange_id1 = ocn.exchange.create(dt.address, to_wei("0.1"), alice_wallet)

    exchange_id2 = ocn.exchange.create(dt.address, to_wei("0.1"), bob_wallet)

    logs = ocn.exchange.search_exchange_by_data_token(dt.address)

    assert logs[0].args.dataToken == dt.address
    assert logs[1].args.dataToken == dt.address
    assert exchange_id1 == logs[0].args.exchangeId
    assert alice_wallet.address == logs[0].args.exchangeOwner
    assert exchange_id2 == logs[1].args.exchangeId
    assert bob_wallet.address == logs[1].args.exchangeOwner


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
    rate = to_wei("0.9")
    x_id = ox.create(dt.address, rate, bob_wallet)
    dt.approve(ox._exchange_address, to_wei(20), bob_wallet)

    # create with invalid token address
    with pytest.raises(ValueError):
        ox.create(ox.ocean_address, rate, bob_wallet)

    # TODO: Enable this ValueError handling when the ERC20 check is added in FixedRateExchange.create solidity function
    # with pytest.raises(ValueError):
    # ox.create(ox._exchange_address, 0.9, bob_wallet)

    # create with negative rate, should fail
    with pytest.raises(AssertionError):
        _ = ox.create(dt.address, -rate, bob_wallet)

    # create using 0 rate
    with pytest.raises(AssertionError):
        _ = ox.create(dt.address, 0, bob_wallet)

    ##############
    # get_quote
    base_token_amount = ox.get_quote(to_wei(2), exchange_id=x_id)
    expected_base_token_amount = to_wei("1.8")  # 2 * 9
    assert (
        base_token_amount == expected_base_token_amount
    ), f"unexpected quote of {pretty_ether_and_wei(base_token_amount, 'OCEAN')}, should be {pretty_ether_and_wei(expected_base_token_amount, 'OCEAN')}."

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

    rate = to_wei(1)
    assert ox.setRate(rate, bob_wallet, exchange_id=x_id)
    # re-evaluate with new rate
    base_token_amount = ox.get_quote(to_wei(2), exchange_id=x_id)
    expected_base_token_amount = to_wei(2)
    assert (
        base_token_amount == expected_base_token_amount
    ), f"unexpected quote of {pretty_ether_and_wei(base_token_amount, 'OCEAN')} base tokens, should be {pretty_ether_and_wei(expected_base_token_amount, 'OCEAN')}."
