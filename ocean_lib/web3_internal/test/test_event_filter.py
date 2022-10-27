#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest

from ocean_lib.web3_internal.event_filter import EventFilter


@pytest.mark.unit
def test_transfer_event_filter(alice_ocean, alice_wallet, bob_address, data_nft):
    data_nft.transfer_from(alice_wallet.address, bob_address, 1, alice_wallet)

    block = alice_ocean.web3.eth.block_number
    event_filter = EventFilter(
        data_nft.events.Transfer(), from_block=block, to_block=block
    )

    assert event_filter.filter_id, "Event filter ID is None."

    event_filter.uninstall()
    event_filter.recreate_filter()

    assert (
        event_filter.get_new_entries() == []
    ), "There are new entries for EventFilter."
