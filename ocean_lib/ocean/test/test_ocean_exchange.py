#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from ocean_lib.config_provider import ConfigProvider
from ocean_lib.models.fixed_rate_exchange import FixedRateExchange
from ocean_lib.ocean.ocean_exchange import OceanExchange
from ocean_lib.ocean.util import get_contracts_addresses
from tests.resources.helper_functions import get_consumer_wallet, get_publisher_wallet

_NETWORK = "ganache"


def _get_exchange_address():
    """Helper function to retrieve a known exchange address."""
    return get_contracts_addresses(_NETWORK, ConfigProvider.get_config())[
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
    dt.mint_tokens(bob_wallet.address, 100.0, alice_wallet)
    ox = OceanExchange(ocn.OCEAN_address, _get_exchange_address(), ocn.config)
    rate = 0.9
    x_id = ox.create(dt.address, rate, bob_wallet)
    dt.approve_tokens(ox._exchange_address, 20, bob_wallet)

    # create with invalid token address
    with pytest.raises(ValueError):
        ox.create(ox.ocean_address, 0.9, bob_wallet)

    # TODO: Enable this ValueError handling when the ERC20 check is added in FixedRateExchange.create solidity function
    # with pytest.raises(ValueError):
    # ox.create(ox._exchange_address, 0.9, bob_wallet)

    # create with negative rate, should fail
    with pytest.raises(AssertionError):
        _ = ox.create(dt.address, rate * -1.0, bob_wallet)

    # create using 0 rate
    with pytest.raises(AssertionError):
        _ = ox.create(dt.address, 0.0, bob_wallet)

    ##############
    # get_quote
    base_token_amount = ox.get_quote(2.0, exchange_id=x_id)
    assert (
        base_token_amount == 2.0 * rate
    ), f"unexpected quote of base token {base_token_amount}, should be {2.0*rate}."

    #############
    # test buying datatokens
    # Alice is buying from exchange owned by bob
    assert (
        ox.buy_at_fixed_rate(
            2.0,
            alice_wallet,
            max_OCEAN_amount=base_token_amount,
            data_token=dt.address,
            exchange_owner=bob_wallet.address,
        )
        is True
    ), "buy datatokens failed"
    assert (
        ox.buy_at_fixed_rate(
            2.0, alice_wallet, max_OCEAN_amount=base_token_amount, exchange_id=x_id
        )
        is True
    ), "buy datatokens failed"

    print("-------- all good --------")
