#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json

from ocean_lib.models.algorithm_metadata import AlgorithmMetadata

algo_metadata_test_dict = {
    "url": "http://test.url",
    "rawcode": "Hello world!",
    "language": "Scala",
    "format": "format",
    "version": "1.0",
    "container": {
        "entrypoint": "some_container_entrypoint",
        "image": "some_image",
        "tag": "some_tag",
    },
}


def test_init_algo_metadata():
    """Tests functions of the AlgorithmMetadata class."""
    algo_metadata = AlgorithmMetadata(algo_metadata_test_dict)
    assert algo_metadata.is_valid() is True
    assert algo_metadata.as_dictionary() == algo_metadata_test_dict
    assert algo_metadata.as_json_str() == json.dumps(algo_metadata_test_dict)
