#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest


@pytest.mark.unit
def test1(ocean):
    # df-py/util/test has thorough tests, so keep it super-simple here
    assert ocean.ve_fee_estimate.address is not None
