#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from ocean_lib.web3_internal.exceptions import (
    OceanDIDNotFound,
    OceanInvalidTransaction,
    OceanKeeperContractsNotFound,
)


def test_exceptions():
    """Tests that exceptions can be raised."""
    with pytest.raises(OceanKeeperContractsNotFound):
        raise OceanKeeperContractsNotFound
    with pytest.raises(OceanDIDNotFound):
        raise OceanDIDNotFound
    with pytest.raises(OceanInvalidTransaction):
        raise OceanInvalidTransaction
