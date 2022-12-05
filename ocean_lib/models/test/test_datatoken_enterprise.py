#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import pytest

from ocean_lib.models.datatoken import Datatoken


@pytest.mark.unit
def test_datatoken_enterprise_1(datatoken_enterprise_token):
    assert isinstance(datatoken_enterprise_token, Datatoken)
