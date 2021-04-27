#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_lib.common.aquarius.aquarius import Aquarius


def test_init():
    aqua = Aquarius("http://something/api/v1/aquarius/assets")
    assert aqua.url == "http://something/api/v1/aquarius/assets/ddo"
    assert aqua.root_url == "http://something"
