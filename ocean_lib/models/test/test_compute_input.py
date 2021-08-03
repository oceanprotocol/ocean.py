#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from ocean_lib.models.compute_input import ComputeInput


def test_init_compute_input():
    """Tests functions of the ComputeInput class."""
    compute_input = ComputeInput("some_did", "some_tx_id", "some_service_id")
    assert compute_input.as_dictionary() == {
        "documentId": "some_did",
        "transferTxId": "some_tx_id",
        "serviceId": "some_service_id",
    }

    with pytest.raises(AssertionError):
        ComputeInput(None, "tx_id", "service_id")

    with pytest.raises(AssertionError):
        ComputeInput("did", "", "service_id")

    with pytest.raises(TypeError):
        ComputeInput("did", "tx_id", "service_id", userdata="not_a_dict")

    userdata = {"test1": "test"}
    compute_input = ComputeInput("did", "tx_id", "service_id", userdata=userdata)

    assert compute_input.as_dictionary()["userdata"] == userdata
