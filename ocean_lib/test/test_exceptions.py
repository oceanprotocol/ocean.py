#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import uuid

import pytest
from ocean_lib.assets.asset import Asset
from ocean_lib.exceptions import InsufficientBalance
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.currency import to_wei
from tests.resources.ddo_helpers import get_resource_path


@pytest.mark.skip(reason="TODO: pay_for_service function on OceanAssets class")
def test_InsufficientBalance(publisher_ocean_instance, publisher_wallet):
    alice = publisher_wallet
    sample_ddo_path = get_resource_path("ddo", "ddo_sa_sample.json")
    asset = Asset(json_filename=sample_ddo_path)
    asset.metadata["main"]["files"][0]["checksum"] = str(uuid.uuid4())

    token = publisher_ocean_instance.create_data_token(
        "DataToken1", "DT1", from_wallet=alice, blob="foo_blob"
    )

    with pytest.raises(InsufficientBalance):
        publisher_ocean_instance.assets.pay_for_service(
            publisher_ocean_instance.web3,
            to_wei("12345678999999.9"),
            token.address,
            asset.did,
            0,
            ZERO_ADDRESS,
            alice,
            alice.address,
        )
