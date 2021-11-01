#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_lib.utils import utilities


def test_convert():
    """Tests convert to string from utilities."""
    input_text = "my text"
    text_bytes = utilities.convert_to_bytes(input_text)
    print("output %s" % utilities.convert_to_string(text_bytes))
    assert input_text == utilities.convert_to_text(text_bytes)
