#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import Any, Dict, List, Optional

from enforce_typing import enforce_types


class FilesType:

    supported_types = ["url", "ipfs", "arweave"]

    @enforce_types
    def __init__(
        self,
        type: str,
        value: str,
        method: Optional[str] = None,
        headers: Optional[List[Dict[str, str]]] = None,
    ):
        if type not in FilesType.supported_types:
            raise ValueError("Unrecognized file type")
        self.type = type
        self.value = value
        self.method = method
        self.headers = headers

    @enforce_types
    @classmethod
    def from_dict(cls, dictionary: Dict[str, Any]) -> "FilesType":
        if type not in FilesType.supported_types:
            raise ValueError("Unrecognized file type")

        return cls(
            dictionary["type"],
            dictionary["value"],
            dictionary.get("method"),
            dictionary.get("headers"),
        )

    @enforce_types
    def to_dict(self) -> Dict[str, Any]:
        result = {"type": self.type, "value": self.value}

        if self.method is not None:
            result["method"] = self.method
        if self.headers is not None:
            result["headers"] = self.headers

        return result
