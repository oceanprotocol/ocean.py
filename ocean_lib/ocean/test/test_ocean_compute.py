#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from unittest.mock import patch

import pytest

from ocean_lib.agreements.service_types import ServiceTypes
from ocean_lib.assets.asset import Asset
from ocean_lib.config import Config
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.ocean.ocean_compute import OceanCompute
from tests.resources.ddo_helpers import get_sample_ddo_with_compute_service


@pytest.mark.unit
def test_get_service_endpoint():
    data_provider = DataServiceProvider
    options_dict = {"resources": {"provider.url": "http://localhost:8030"}}
    config = Config(options_dict=options_dict)
    compute = OceanCompute(config, data_provider)

    ddo = Asset.from_dict(get_sample_ddo_with_compute_service())
    compute_service = ddo.get_service(ServiceTypes.CLOUD_COMPUTE)
    compute_service.service_endpoint = "http://localhost:8030"

    with patch("ocean_lib.ocean.ocean_compute.resolve_asset") as mock:
        mock.return_value = ddo
        service_endpoint = compute._get_service_endpoint(ddo.did)

    assert service_endpoint, "The service endpoint is None."
    assert isinstance(service_endpoint, tuple), "The service endpoint is not a tuple."
    assert (
        service_endpoint[0] == "GET"
    ), "The http method of compute status job must be GET."
    assert (
        service_endpoint[1]
        == data_provider.build_compute_endpoint(config.provider_url)[1]
    ), "Different URLs for compute status job."
