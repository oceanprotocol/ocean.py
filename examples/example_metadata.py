#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import uuid

metadata = {
    "main": {
        "name": "Ocean protocol white paper",
        "dateCreated": "2012-02-01T10:55:11Z",
        "author": "Mario",
        "license": "CC0: Public Domain",
        "files": [
            {
                "index": 0,
                "contentType": "text/text",
                "checksum": str(uuid.uuid4()),
                "checksumType": "MD5",
                "contentLength": "12057507",
                "url": "https://raw.githubusercontent.com/oceanprotocol/barge/master/README.md",
            }
        ],
        "type": "dataset",
    }
}

algo_metadata = {
    "url": "https://raw.githubusercontent.com/oceanprotocol/test-algorithm/master/javascript/algo.js",
    "language": "js",
    "format": "docker-image",
    "version": "v0.0.1",
    "container": {"entrypoint": "node $ALGO", "image": "node", "tag": "10"},
}
