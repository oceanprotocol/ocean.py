#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from ocean_lib.web3_internal.web3_overrides.contract import wait_for_tx
from web3.utils.threads import Timeout


def test_wait_for_tx_failures(alice_ocean):
    with pytest.raises(ValueError):
        wait_for_tx("TXisnotAHash", alice_ocean.web3)

    with pytest.raises(Timeout):
        # transaction does not exist, it will timeout regardless of the timeout value
        wait_for_tx("0x0", alice_ocean.web3, 1)
