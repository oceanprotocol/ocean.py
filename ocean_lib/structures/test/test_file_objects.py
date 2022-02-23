#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest

from ocean_lib.structures.file_objects import FilesTypeFactory, IpfsFile, UrlFile


@pytest.mark.unit
def test_url_file():
    url_file = UrlFile(url="https://url.com")
    assert url_file.to_dict() == {"type": "url", "url": "https://url.com"}

    url_file = UrlFile(url="https://url.com", method="POST")
    assert url_file.to_dict() == {
        "type": "url",
        "url": "https://url.com",
        "method": "POST",
    }


@pytest.mark.unit
def test_ipfs_file():
    ipfs_file = IpfsFile(hash="abc")
    assert ipfs_file.to_dict() == {"type": "ipfs", "hash": "abc"}


@pytest.mark.unit
def test_filetype_factory():
    factory_file = FilesTypeFactory(
        {
            "type": "url",
            "url": "https://url.com",
            "method": "GET",
        }
    )

    assert factory_file.url == "https://url.com"

    factory_file = FilesTypeFactory(
        {
            "type": "ipfs",
            "hash": "abc",
        }
    )

    assert factory_file.hash == "abc"

    with pytest.raises(Exception):
        factory_file = FilesTypeFactory({"type": "somethingelse"})
