#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json


class AlgorithmMetadata:
    def __init__(self, metadata_dict):
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

    def is_valid(self):
        return bool(
            self.container_image and self.container_tag and self.container_entry_point
        )

    def as_json_str(self):
        return json.dumps(self.as_dictionary())

    def as_dictionary(self):
        return {
            "url": self.url,
            "rawcode": self.rawcode,
            "language": self.language,
            "format": self.format,
            "version": self.version,
            "container": {
                "entrypoint": self.container_entry_point,
                "image": self.container_image,
                "tag": self.container_tag,
            },
        }
