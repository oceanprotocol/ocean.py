#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from unittest.mock import patch

import pytest

from ocean_lib.assets.asset import Asset
from ocean_lib.services.service import Service
from tests.resources.ddo_helpers import get_sample_ddo


@pytest.mark.unit
def test_service():
    """Tests that the get_cost function for ServiceAgreement returns the correct value."""
    ddo_dict = get_sample_ddo()
    service_dict = ddo_dict["services"][0]
    sa = Service.from_dict(service_dict)

    assert sa.id == "1"
    assert sa.name == "Download service"
    assert sa.type == "access"
    assert sa.service_endpoint == "https://myprovider.com"
    assert sa.datatoken == "0x123"

    assert sa.as_dictionary() == {
        "id": "1",
        "type": "access",
        "serviceEndpoint": "https://myprovider.com",
        "datatokenAddress": "0x123",
        "files": "0x0000",
        "timeout": 0,
        "name": "Download service",
        "description": "Download service",
    }

    ddo_dict = get_sample_ddo()
    service_dict = ddo_dict["services"][0]
    del service_dict["type"]
    with pytest.raises(IndexError):
        Service.from_dict(service_dict)

    ddo_dict = get_sample_ddo()
    asset = Asset.from_dict(ddo_dict)
    with patch(
        "ocean_lib.services.service.DataServiceProvider.check_asset_file_info"
    ) as mock:
        mock.return_value = False
        assert sa.is_consumable(asset, {}, True) == 2

    with patch(
        "ocean_lib.services.service.DataServiceProvider.check_asset_file_info"
    ) as mock:
        mock.return_value = True
        assert (
            sa.is_consumable(asset, {"type": "address", "value": "0xdddd"}, True) == 3
        )
