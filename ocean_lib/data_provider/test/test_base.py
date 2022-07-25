#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_lib.data_provider.base import DataServiceProviderBase


def test_sanitize_content_disposition():
    header = "./../../my/relative/path"
    res = DataServiceProviderBase._sanitize_content(header)
    assert res is False

    header = "somehtml.html"
    res = DataServiceProviderBase._sanitize_content(header)
    assert res is True
