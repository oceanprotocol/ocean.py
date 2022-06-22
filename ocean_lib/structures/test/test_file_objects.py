#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest

from ocean_lib.structures.file_objects import FilesType


@pytest.mark.unit
def test_url_file():
    url_file = FilesType(file_type="url", value="https://url.com")
    assert url_file.to_dict() == {"type": "url", "value": "https://url.com"}

    url_file = FilesType(file_type="url", value="https://url.com", method="POST")
    assert url_file.to_dict() == {
        "type": "url",
        "value": "https://url.com",
        "method": "POST",
    }

    url_file = FilesType(
        file_type="url",
        value="https://url.com",
        headers=[{"Authorization": "Bearer 123"}, {"APIKEY": "124"}],
    )
    assert url_file.to_dict() == {
        "type": "url",
        "value": "https://url.com",
        "headers": [{"Authorization": "Bearer 123"}, {"APIKEY": "124"}],
    }


@pytest.mark.unit
def test_ipfs_file():
    ipfs_file = FilesType(file_type="ipfs", value="abc")
    assert ipfs_file.to_dict() == {"type": "ipfs", "value": "abc"}


@pytest.mark.unit
def test_arweave_file():
    arweave_file = FilesType(
        file_type="arweave", value="cZ6j5PmPVXCq5Az6YGcGqzffYjx2JnsnlSajaHNr20w"
    )
    assert arweave_file.to_dict() == {
        "type": "arweave",
        "value": "cZ6j5PmPVXCq5Az6YGcGqzffYjx2JnsnlSajaHNr20w",
    }


@pytest.mark.unit
def test_filestype_from_dict():
    factory_file = FilesType.from_dict(
        {
            "type": "url",
            "value": "https://url.com",
            "method": "GET",
        }
    )

    assert factory_file.type == "url"
    assert factory_file.value == "https://url.com"
    assert factory_file.method == "GET"

    factory_file = FilesType.from_dict(
        {
            "type": "ipfs",
            "value": "abc",
        }
    )

    assert factory_file.type == "ipfs"
    assert factory_file.value == "abc"

    factory_file = FilesType.from_dict(
        {
            "type": "arweave",
            "value": "cZ6j5PmPVXCq5Az6YGcGqzffYjx2JnsnlSajaHNr20w",
        }
    )

    assert factory_file.type == "arweave"
    assert factory_file.value == "cZ6j5PmPVXCq5Az6YGcGqzffYjx2JnsnlSajaHNr20w"

    with pytest.raises(ValueError):
        factory_file = FilesType.from_dict({"type": "somethingelse"})
