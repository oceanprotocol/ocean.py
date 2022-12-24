#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest


@pytest.mark.unit
def test1(ocean, consumer_wallet):
    # df-py/util/test/veOcean/test_estimateClaim.py has thorough tests
    # therefore, we keep it super-simple here
    assert ocean.ve_fee_distributor.address is not None

    ocean.ve_fee_distributor.user_epoch_of(consumer_wallet)
    ocean.ve_fee_distributor.time_cursor_of(consumer_wallet)

    # this is the most important call from a user standpoint. $$ :)
    ocean.ve_fee_distributor.claim({"from": consumer_wallet})
