#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from abc import abstractmethod
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


class IpfsFile(FilesType):
    @enforce_types
    def __init__(self, hash: str) -> None:
        self.hash = hash
        self.type = "ipfs"

    @enforce_types
    def to_dict(self) -> dict:
        return {"type": self.type, "hash": self.hash}


class GraphqlQuery(FilesType):
    @enforce_types
    def __init__(self, url: str, query: str, headers: Optional[dict] = None) -> None:
        self.url = url
        self.query = query
        self.headers = headers
        self.type = "graphql"

    @enforce_types
    def to_dict(self) -> dict:
        result = {"type": self.type, "url": self.url, "query": self.query}

        if self.headers:
            result["headers"] = self.headers

        return result


class SmartContractCall(FilesType):
    @enforce_types
    def __init__(self, address: str, chainId: int, abi: dict) -> None:
        self.address = address
        self.abi = abi
        self.chainId = chainId
        self.type = "smartcontract"

    @enforce_types
    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "address": self.address,
            "abi": self.abi,
            "chainId": self.chainId,
        }


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
    elif file_obj["type"] == "graphql":
        return GraphqlQuery(file_obj["url"], query=file_obj.get("query"))
    elif file_obj["type"] == "smartcontract":
        return SmartContractCall(
            address=file_obj.get("address"),
            chainId=file_obj.get("chainId"),
            abi=file_obj.get("abi"),
        )
    else:
        raise Exception("Unrecognized file type")
