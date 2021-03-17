#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_lib.models.data_token import DataToken
from ocean_lib.models.dtfactory import DTFactory
from ocean_lib.ocean.util import to_base_18


def test_data_token_creation(network, alice_wallet, dtfactory_address, alice_ocean):
    """Tests that a data token can be created using a DTFactory object."""
    dtfactory = DTFactory(dtfactory_address)

    dt_address = dtfactory.createToken(
        "foo_blob", "DT1", "DT1", to_base_18(1000), from_wallet=alice_wallet
    )
    dt = DataToken(dtfactory.get_token_address(dt_address))
    assert isinstance(dt, DataToken)
    assert dt.blob() == "foo_blob"
    assert dtfactory.verify_data_token(dt.address)


def test_data_token_event_registered(
    network, alice_wallet, dtfactory_address, alice_ocean
):
    """Tests that a token registration event is created and can be retrieved."""
    dtfactory = DTFactory(dtfactory_address)

    dt_address = dtfactory.createToken(
        "foo_blob", "DT1", "DT1", to_base_18(1000), from_wallet=alice_wallet
    )
    dt = DataToken(dtfactory.get_token_address(dt_address))
    block = alice_ocean.web3.eth.blockNumber

    # with explicit address
    registered_event = dtfactory.get_token_registered_event(
        block - 1, block + 1, token_address=dt.address
    )

    assert registered_event.args.tokenAddress == dt.address

    # without explicit address, no metadata_url and no sender
    registered_event = dtfactory.get_token_registered_event(block - 1, block + 1)

    assert registered_event is None

    # TODO: provide metadata_url and sender to return the correct event
    # still pending because I don't know how blob is encoded in the log args


# TODO: test_get_token_minter...


def test_get_token_address_fails(network, alice_wallet, dtfactory_address, alice_ocean):
    """Tests the failure case for get_token_address."""
    dtfactory = DTFactory(dtfactory_address)

    assert dtfactory.get_token_address("") == ""
