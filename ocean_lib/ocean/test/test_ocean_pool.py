#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_lib.ocean.util import get_ocean_token_address
from ocean_lib.web3_internal.web3helper import Web3Helper


def test_get_OCEAN_address(publisher_ocean_instance):
    """Tests OCEAN address retrieval."""
    network = Web3Helper.get_network_name()
    assert publisher_ocean_instance.pool.get_OCEAN_address() == get_ocean_token_address(
        network
    )
