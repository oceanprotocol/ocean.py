#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from unittest.mock import patch

import pytest
from ocean_lib.models.data_token import DataToken
from ocean_lib.models.dtfactory import DTFactory
from ocean_lib.web3_internal.currency import to_wei
from web3.exceptions import TimeExhausted


def test_data_token_creation(web3, alice_wallet, dtfactory_address):
    """Tests that a data token can be created using a DTFactory object."""
    dtfactory = DTFactory(web3, dtfactory_address)

    dt_address = dtfactory.createToken(
        "foo_blob", "DT1", "DT1", to_wei(1000), from_wallet=alice_wallet
    )
    dt = DataToken(web3, dtfactory.get_token_address(dt_address))
    assert isinstance(dt, DataToken)
    assert dt.blob() == "foo_blob"
    assert dtfactory.verify_data_token(dt.address)


def test_data_token_event_registered(
    web3, alice_wallet, dtfactory_address, alice_ocean
):
    """Tests that a token registration event is created and can be retrieved."""
    dtfactory = DTFactory(web3, dtfactory_address)

    dt_address = dtfactory.createToken(
        "foo_blob", "DT1", "DT1", to_wei(1000), from_wallet=alice_wallet
    )
    dt = DataToken(web3, dtfactory.get_token_address(dt_address))
    block = alice_ocean.web3.eth.block_number

    # with explicit address
    block_confirmations = alice_ocean.config.block_confirmations.value
    registered_event = dtfactory.get_token_registered_event(
        block - (block_confirmations + 1), block, token_address=dt.address
    )

    assert registered_event.args.tokenAddress == dt.address


def test_get_token_address_fails(web3, dtfactory_address):
    """Tests the failure case for get_token_address."""
    dtfactory = DTFactory(web3, dtfactory_address)
    # Transaction 0x is not in the chain
    with pytest.raises(TimeExhausted):
        with patch("ocean_lib.models.dtfactory.DTFactory.get_tx_receipt") as mock:
            # throw the exception without acually waiting
            mock.side_effect = TimeExhausted()
            # we are checking that this exception bubbles up to get_token_address()
            dtfactory.get_token_address("")


def test_get_token_minter(web3, alice_wallet, dtfactory_address, alice_address):
    """Tests proper retrieval of token minter from DTFactory."""
    dtfactory = DTFactory(web3, dtfactory_address)

    dt_address = dtfactory.createToken(
        "foo_blob", "DT1", "DT1", to_wei(1000), from_wallet=alice_wallet
    )
    dt = DataToken(web3, dtfactory.get_token_address(dt_address))
    dt.mint(alice_address, to_wei(10), from_wallet=alice_wallet)
    assert dtfactory.get_token_minter(dt.address) == alice_address
