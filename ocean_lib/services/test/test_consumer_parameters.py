#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest

from ocean_lib.services.consumer_parameters import ConsumerParameters


@pytest.mark.unit
def test_consumer_parameters():
    """Tests the Consumer Parameters key/object."""
    cp_dict = {
        "name": "test_key",
        "type": "string",
        "label": "test_key_label",
        "required": True,
        "default": "value",
        "description": "this is a test key",
        "options": ["a", "b"],
    }

    cp_object = ConsumerParameters.from_dict(cp_dict)
    assert cp_object.as_dictionary() == cp_dict

    cp_dict.pop("options")
    cp_object = ConsumerParameters.from_dict(cp_dict)
    assert cp_object.as_dictionary() == cp_dict

    cp_dict["required"] = "false"  # explicitly false, not missing
    cp_object = ConsumerParameters.from_dict(cp_dict)
    assert cp_object.as_dictionary()["required"] is False

    cp_dict["options"] = "not an array"
    with pytest.raises(TypeError):
        cp_object = ConsumerParameters.from_dict(cp_dict)

    cp_dict.pop("options")
    cp_dict.pop("type")
    cp_dict.pop("label")
    with pytest.raises(TypeError, match="is missing the keys type, label"):
        cp_object = ConsumerParameters.from_dict(cp_dict)
