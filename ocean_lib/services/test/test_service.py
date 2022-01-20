#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_lib.agreements.service_types import ServiceTypes
from ocean_lib.assets.asset import Asset
from tests.resources.ddo_helpers import get_sample_ddo


def test_service():
    """Tests that the get_cost function for ServiceAgreement returns the correct value."""
    ddo = Asset.from_dict(get_sample_ddo())
    sa = ddo.get_service(ServiceTypes.ASSET_ACCESS)
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
