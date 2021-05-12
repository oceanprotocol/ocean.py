#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import uuid

import pytest
from eth_utils import add_0x_prefix

from ocean_lib.common.ddo.ddo import DDO
from ocean_lib.exceptions import InsufficientBalance, ContractNotFound
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from tests.resources.ddo_helpers import get_resource_path
from tests.resources.helper_functions import get_publisher_wallet


def test_OceanEncryptAssetUrlsError():
    pass


def test_InsufficientBalance(publisher_ocean_instance):
    alice = get_publisher_wallet()
    sample_ddo_path = get_resource_path("ddo", "ddo_sa_sample.json")
    asset = DDO(json_filename=sample_ddo_path)
    asset.metadata["main"]["files"][0]["checksum"] = str(uuid.uuid4())

    token = publisher_ocean_instance.create_data_token(
        "DataToken1", "DT1", from_wallet=alice, blob="foo_blob"
    )

    try:
        publisher_ocean_instance.assets.pay_for_service(
            12345678999999.9, token.address, asset.did, 0, ZERO_ADDRESS, alice
        )
    except Exception as e:
        assert type(e) == InsufficientBalance


def test_ContractNotFound(publisher_ocean_instance, metadata):
    publisher = get_publisher_wallet()
    metadata_copy = metadata.copy()

    did = publisher_ocean_instance.assets._get_aquarius().list_assets()[0]
    with pytest.raises(ContractNotFound):
        publisher_ocean_instance.assets.create(
            metadata_copy, publisher, data_token_address=add_0x_prefix(did[7:])
        )


def test_AquariusError(publisher_ocean_instance, metadata):
    pass


def test_VerifyTxFailed(publisher_ocean_instance):
    pass
