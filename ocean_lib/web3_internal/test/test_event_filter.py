#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

from ocean_lib.web3_internal.currency import to_wei
from ocean_lib.web3_internal.event_filter import EventFilter


def test_transfer_event_filter(alice_ocean, alice_wallet, alice_address, bob_address):
    token = alice_ocean.create_data_token(
        "DataToken1", "DT1", from_wallet=alice_wallet, blob="foo_blob"
    )

    token.mint(alice_address, to_wei(100), from_wallet=alice_wallet)
    token.approve(bob_address, to_wei(1), from_wallet=alice_wallet)
    token.transfer(bob_address, to_wei(5), from_wallet=alice_wallet)

    block = alice_ocean.web3.eth.block_number
    event_filter = EventFilter(
        token.events.Transfer(), from_block=block, to_block=block
    )

    assert event_filter.filter_id, "Event filter ID is None."

    event_filter.uninstall()
    event_filter.recreate_filter()

    assert (
        event_filter.get_new_entries() == []
    ), "There are new entries for EventFilter."
