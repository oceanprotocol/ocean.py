#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_lib.data_provider.base import DataServiceProviderBase


def test_sanitize_content_disposition():
    header = "./../../my/relative/path"
    res = DataServiceProviderBase._validate_content_disposition(header)
    assert not res

    header = "somehtml.html"
    res = DataServiceProviderBase._validate_content_disposition(header)
    assert res
