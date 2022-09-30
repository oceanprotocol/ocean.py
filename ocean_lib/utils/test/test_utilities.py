#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest

from ocean_lib.utils import utilities
from ocean_lib.utils.utilities import get_chain_id_from_url


@pytest.mark.unit
def test_convert():
    """Tests convert to string from utilities."""
    input_text = "my text"
    text_bytes = utilities.convert_to_bytes(input_text)
    print("output %s" % utilities.convert_to_string(text_bytes))
    assert input_text == utilities.convert_to_text(text_bytes)


@pytest.mark.unit
def test_chain_id_from_url(config):
    chain_id = get_chain_id_from_url(config["RPC_URL"])
    assert isinstance(chain_id, int)
    assert chain_id == 8996
