#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_lib.models.data_token import DataToken
from ocean_lib.models.dtfactory import DTFactory
from ocean_lib.ocean.util import to_base_18


def test_data_token_creation(network, alice_wallet, dtfactory_address):
    """Tests that a data token can be created using a DTFactory object."""
    dtfactory = DTFactory(dtfactory_address)

    dt_address = dtfactory.createToken(
        "foo_blob", "DT1", "DT1", to_base_18(1000), from_wallet=alice_wallet
    )
    dt = DataToken(dtfactory.get_token_address(dt_address))
    assert isinstance(dt, DataToken)
    assert dt.blob() == "foo_blob"
