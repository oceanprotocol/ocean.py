#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json
from typing import Any, Dict

from enforce_typing import enforce_types

from ocean_lib.services.consumer_parameters import ConsumerParameters


class AlgorithmMetadata:
    @enforce_types
    def __init__(self, metadata_dict: Dict[str, Any]) -> None:
        """Initialises AlgorithmMetadata object."""
        self.url = metadata_dict.get("url", "")
        self.rawcode = metadata_dict.get("rawcode", "")
        self.language = metadata_dict.get("language", "")
        self.format = metadata_dict.get("format", "")
        self.version = metadata_dict.get("version", "")

        container = metadata_dict.get("container", dict())
        self.container_entry_point = container.get("entrypoint", "")
        self.container_image = container.get("image", "")
        self.container_tag = container.get("tag", "")
        self.container_checksum = container.get("checksum", "")

        consumer_parameters = metadata_dict.get("consumerParameters", [])
        try:
            self.consumer_parameters = [
                ConsumerParameters.from_dict(cp_dict) for cp_dict in consumer_parameters
            ]
        except AttributeError:
            raise TypeError("ConsumerParameters should be a list of dictionaries.")

    @enforce_types
    def is_valid(self) -> bool:
        return bool(
            self.container_image and self.container_tag and self.container_entry_point
        )

    @enforce_types
    def as_json_str(self) -> str:
        return json.dumps(self.as_dictionary())

    @enforce_types
    def as_dictionary(self) -> Dict[str, Any]:
        result = {
            "meta": {
                "url": self.url,
                "rawcode": self.rawcode,
                "language": self.language,
                "version": self.version,
                "container": {
                    "entrypoint": self.container_entry_point,
                    "image": self.container_image,
                    "tag": self.container_tag,
                    "checksum": self.container_checksum,
                },
            }
        }

        if self.consumer_parameters:
            consumer_parameters = [x.as_dictionary() for x in self.consumer_parameters]
            result["meta"]["consumerParameters"] = consumer_parameters

        return result
