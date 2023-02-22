#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest


@pytest.mark.unit
def test1(ocean):
    # df-py/util/test has thorough tests, so keep it super-simple here
    assert ocean.df_rewards.address is not None
