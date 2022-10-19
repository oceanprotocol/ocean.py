#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest

from ocean_lib.web3_internal.transactions import send_ether


@pytest.mark.unit
def test_send_ether(alice_wallet, bob_address, config):
    assert send_ether(
        config, alice_wallet, bob_address, "1 ether"
    ), "Send ether was unsuccessful."
