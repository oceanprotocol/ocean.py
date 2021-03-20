#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_lib.ocean.util import get_ocean_token_address
from ocean_lib.web3_internal.web3helper import Web3Helper
from tests.resources.helper_functions import get_publisher_wallet


def test_get_OCEAN_address(publisher_ocean_instance):
    """Tests OCEAN address retrieval."""
    network = Web3Helper.get_network_name()
    assert publisher_ocean_instance.pool.get_OCEAN_address() == get_ocean_token_address(
        network
    )


def test_add_remove_zero_liquidity(publisher_ocean_instance):
    """Tests that adding or removing zero liquidity has no effect."""
    assert (
        publisher_ocean_instance.pool._add_liquidity(
            "addr", "an_addr", 0, get_publisher_wallet()
        )
        == ""
    )
    assert (
        publisher_ocean_instance.pool._remove_liquidity(
            "addr", "an_addr", 0, 1, get_publisher_wallet()
        )
        == ""
    )
