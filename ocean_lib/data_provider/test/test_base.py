#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from requests.models import Response

from ocean_lib.data_provider.base import DataServiceProviderBase


def test_validate_content_disposition():
    header = "./../../my/relative/path"
    res = DataServiceProviderBase._validate_content_disposition(header)
    assert not res

    header = "somehtml.html"
    res = DataServiceProviderBase._validate_content_disposition(header)
    assert res


def test_get_file_name(caplog):
    response = Response()

    response.headers["content-disposition"] = "./../../my/relative/path"
    file_name = DataServiceProviderBase._get_file_name(response)
    assert not file_name
    assert (
        "Invalid content disposition format. It was not possible to get the file name."
        in caplog.text
    )

    response.headers["content-disposition"] = "attachment;filename=somehtml.html"
    file_name = DataServiceProviderBase._get_file_name(response)
    assert file_name == "somehtml.html"
