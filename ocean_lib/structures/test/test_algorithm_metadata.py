#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json

import pytest

from ocean_lib.structures.algorithm_metadata import AlgorithmMetadata


@pytest.mark.unit
def test_algorithm_metadata():
    algo_metadata = AlgorithmMetadata(
        {
            "rawcode": "",
            "language": "Node.js",
            "format": "docker-image",
            "version": "0.1",
            "container": {
                "entrypoint": "node $ALGO",
                "image": "ubuntu",
                "tag": "latest",
                "checksum": "44e10daa6637893f4276bb8d7301eb35306ece50f61ca34dcab550",
            },
        }
    )

    assert algo_metadata.is_valid()
    assert "rawcode" in json.loads(algo_metadata.as_json_str())["meta"]
