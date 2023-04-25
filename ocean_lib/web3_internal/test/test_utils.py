#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from unittest.mock import Mock

import pytest
from brownie.network.account import ClefAccount

from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.utils import sign_with_clef


@pytest.mark.unit
def test_sign_with_clef():
    provider = Mock()
    provider.make_request.return_value = {"jsonrpc": "2.0", "id": 1, "result": "0x1234"}

    wallet = ClefAccount(ZERO_ADDRESS, provider)

    assert sign_with_clef("custom_message", wallet) == "0x1234"
