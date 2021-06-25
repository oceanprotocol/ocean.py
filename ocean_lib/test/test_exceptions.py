#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import uuid

import pytest
from eth_utils import add_0x_prefix

from ocean_lib.common.ddo.ddo import DDO
from ocean_lib.exceptions import InsufficientBalance, ContractNotFound, AquariusError
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from tests.resources.ddo_helpers import get_resource_path, wait_for_ddo
from tests.resources.helper_functions import get_publisher_wallet


def test_InsufficientBalance(publisher_ocean_instance):
    alice = get_publisher_wallet()
    sample_ddo_path = get_resource_path("ddo", "ddo_sa_sample.json")
    asset = DDO(json_filename=sample_ddo_path)
    asset.metadata["main"]["files"][0]["checksum"] = str(uuid.uuid4())

    token = publisher_ocean_instance.create_data_token(
        "DataToken1", "DT1", from_wallet=alice, blob="foo_blob"
    )

    with pytest.raises(InsufficientBalance):
        publisher_ocean_instance.assets.pay_for_service(
            12345678999999.9, token.address, asset.did, 0, ZERO_ADDRESS, alice
        )


def test_ContractNotFound(publisher_ocean_instance, metadata):
    publisher = get_publisher_wallet()
    metadata_copy = metadata.copy()

    # used a random address from Etherscan
    token_address = "0xB3b8239719403E38de3bdF19B9AC147B48c72BF2"
    with pytest.raises(ContractNotFound):
        publisher_ocean_instance.assets.create(
            metadata_copy, publisher, data_token_address=token_address
        )


def test_AquariusError(publisher_ocean_instance, metadata):
    metadata_copy = metadata.copy()
    publisher = get_publisher_wallet()

    all_assets = publisher_ocean_instance.assets._get_aquarius().list_assets()

    if not all_assets:
        # the test is run in isolation, docker has been pruned,
        # or Aqua is empty for some other reason
        ddo = publisher_ocean_instance.assets.create(metadata_copy, publisher)
        wait_for_ddo(publisher_ocean_instance, ddo.did)
        all_assets = publisher_ocean_instance.assets._get_aquarius().list_assets()

    did = all_assets[0]
    token_address = add_0x_prefix(did[7:])

    with pytest.raises(AquariusError):
        publisher_ocean_instance.assets.create(
            metadata_copy, publisher, data_token_address=token_address
        )
