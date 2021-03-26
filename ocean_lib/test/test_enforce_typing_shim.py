#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import pytest

from ocean_lib.enforce_typing_shim import enforce_types_shim

@enforce_types_shim
def func(arg: str):
    return

def test_enforce_types_enabled():
    """Tests that enforce_types_shim is currently enabled."""
    with pytest.raises(TypeError):
        func(1)
