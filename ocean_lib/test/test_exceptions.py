#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import uuid
from unittest.mock import patch

import pytest
from ocean_lib.assets.asset import V3Asset
from ocean_lib.exceptions import AquariusError, ContractNotFound, InsufficientBalance
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.currency import to_wei
from tests.resources.ddo_helpers import get_resource_path
from tests.resources.helper_functions import get_publisher_wallet


def test_InsufficientBalance(publisher_ocean_instance):
    alice = get_publisher_wallet()
    sample_ddo_path = get_resource_path("ddo", "ddo_sa_sample.json")
    asset = V3Asset(json_filename=sample_ddo_path)
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


def test_ContractNotFound(publisher_ocean_instance, metadata):
    publisher = get_publisher_wallet()
    metadata_copy = metadata.copy()

    # used a random address from Etherscan
    token_address = "0xB3b8239719403E38de3bdF19B9AC147B48c72BF2"
    with patch("ocean_lib.models.dtfactory.DTFactory.verify_data_token") as mock:
        mock.return_value = False
        with pytest.raises(ContractNotFound):
            publisher_ocean_instance.assets.create(
                metadata_copy, publisher, data_token_address=token_address
            )


def test_AquariusError(publisher_ocean_instance, metadata):
    metadata_copy = metadata.copy()
    publisher = get_publisher_wallet()

    ocn = publisher_ocean_instance
    alice_wallet = get_publisher_wallet()
    dt = ocn.create_data_token(
        "DataToken1", "DT1", alice_wallet, blob=ocn.config.metadata_cache_uri
    )

    with patch("ocean_lib.common.aquarius.aquarius.Aquarius.ddo_exists") as mock:
        mock.return_value = True
        with pytest.raises(AquariusError):
            publisher_ocean_instance.assets.create(
                metadata_copy, publisher, data_token_address=dt.address
            )
