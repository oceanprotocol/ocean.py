#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import Optional, Union

from enforce_typing import enforce_types


class UrlFile(object):
    @enforce_types
    def __init__(self, url: str, method: Optional[str] = None) -> None:
        self.url = url
        self.method = method
        self.type = "url"

    @enforce_types
    def to_dict(self) -> dict:
        result = {"type": self.type, "url": self.url}

        if self.method:
            result["method"] = self.method

        return result


class IpfsFile(object):
    @enforce_types
    def __init__(self, hash: str) -> None:
        self.hash = hash
        self.type = "ipfs"

    @enforce_types
    def to_dict(self) -> dict:
        return {"type": self.type, "hash": self.hash}


@enforce_types
def FilesTypeFactory(file_obj: dict) -> Union[UrlFile, IpfsFile]:
    """Factory Method"""
    if file_obj["type"] == "url":
        return UrlFile(file_obj["url"], file_obj["method"])
    elif file_obj["type"] == "ipfs":
        return IpfsFile(file_obj["hash"])
    else:
        raise Exception("Unrecognized file type")
