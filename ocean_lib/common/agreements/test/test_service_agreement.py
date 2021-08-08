#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from ocean_lib.common.agreements.service_agreement import ServiceAgreement
from ocean_lib.common.agreements.service_types import ServiceTypes
from tests.resources.ddo_helpers import get_sample_ddo


def test_no_service_key_ddo(publisher_ocean_instance, metadata):
    """Tests that ServiceAgreements are not created with bad indices."""
    # from init
    with pytest.raises(TypeError):
        ServiceAgreement(attributes=None, service_index="not_a_real_index")

    # from ddo
    ddo = get_sample_ddo()
    with pytest.raises(ValueError):
        ServiceAgreement.from_ddo(service_type="not_a_real_index", ddo=ddo)


def test_cost():
    """Tests that the get_cost function for ServiceAgreement returns the correct value."""
    ddo = get_sample_ddo()
    sa = ServiceAgreement.from_ddo(service_type=ServiceTypes.ASSET_ACCESS, ddo=ddo)
    assert sa.get_cost() == 1.0
