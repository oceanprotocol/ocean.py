#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest

from ocean_lib.web3_internal.event_filter import EventFilter
from tests.resources.helper_functions import deploy_erc721_erc20


@pytest.mark.unit
def test_transfer_event_filter(
    alice_ocean, config, alice_wallet, alice_address, bob_address
):
    erc721, erc20 = deploy_erc721_erc20(
        alice_ocean.web3, config, alice_wallet, alice_wallet
    )

    erc721.transfer_from(alice_wallet.address, bob_address, 1, alice_wallet)

    block = alice_ocean.web3.eth.block_number
    event_filter = EventFilter(
        erc721.events.Transfer(), from_block=block, to_block=block
    )

    assert event_filter.filter_id, "Event filter ID is None."

    event_filter.uninstall()
    event_filter.recreate_filter()

    assert (
        event_filter.get_new_entries() == []
    ), "There are new entries for EventFilter."
