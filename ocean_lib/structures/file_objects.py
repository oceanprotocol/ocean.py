#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from abc import abstractmethod
import os
from typing import Optional, Protocol

from enforce_typing import enforce_types


class FilesType(Protocol):
    @enforce_types
    @abstractmethod
    def to_dict(self) -> dict:
        raise NotImplementedError


class UrlFile(FilesType):
    @enforce_types
    def __init__(
        self, url: str, method: Optional[str] = None, headers: Optional[dict] = None
    ) -> None:
        self.url = url
        self.method = method
        self.headers = headers
        self.type = "url"

    @enforce_types
    def to_dict(self) -> dict:
        result = {"type": self.type, "url": self.url}

        if self.method:
            result["method"] = self.method

        if self.headers:
            result["headers"] = self.headers

        return result


class FilecoinFile(object):
    @enforce_types
    def __init__(self, hash: str) -> None:
        self.hash = hash
        self.type = "filecoin"

    @enforce_types
    def to_dict(self) -> dict:
        return {"type": self.type, "hash": self.hash}


class IpfsFile(FilesType):
    @enforce_types
    def __init__(self, hash: str) -> None:
        self.hash = hash
        self.type = "ipfs"
        self.gateway = os.getenv("IPFS_GATEWAY")
        self.url = self.get_download_url()

    @enforce_types
    def to_dict(self) -> dict:
        return {"type": self.type, "hash": self.hash, "url": self.url, "gateway": self.gateway}

    def get_download_url(self):
        if not self.gateway:
            raise Exception("No IPFS_GATEWAY defined, can not resolve ipfs hash.")

        if self.gateway == "https://api.web3.storage/upload":
            url = f"https://{self.hash}.ipfs.dweb.link"
        elif self.gateway in ["https://api.estuary.tech/content/add", "https://shuttle-5.estuary.tech/content/add"]:
            url = f'https://dweb.link/ipfs/{cid}'
        else:
            url = urljoin(os.getenv("IPFS_GATEWAY"), urljoin("ipfs/", self.hash))

        return url

@enforce_types
def FilesTypeFactory(file_obj: dict) -> FilesType:
    """Factory Method"""
    if file_obj["type"] == "url":
        return UrlFile(
            file_obj["url"],
            method=file_obj.get("method", "GET"),
            headers=file_obj.get("headers"),
        )
    elif file_obj["type"] == "ipfs":
        return IpfsFile(file_obj["hash"])
    else:
        raise Exception("Unrecognized file type")
