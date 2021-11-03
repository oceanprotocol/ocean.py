#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_lib.common.agreements.service_types import ServiceTypes
from ocean_lib.services.service import Service
from tests.resources.ddo_helpers import get_sample_ddo


def test_service():
    """Tests that the get_cost function for ServiceAgreement returns the correct value."""
    ddo = get_sample_ddo()
    sa = ddo.get_service(ServiceTypes.ASSET_ACCESS)
    assert sa.get_cost() == 1.0
    assert sa.get_c2d_address()
    assert sa.main["name"] == "dataAssetAccessServiceAgreement"

    assert "attributes" in sa.as_dictionary()
    converted = Service.from_json(sa.as_dictionary())
    assert converted.attributes == sa.attributes
    assert converted.service_endpoint == sa.service_endpoint
    assert converted.type == sa.type
    assert converted.index == sa.index
