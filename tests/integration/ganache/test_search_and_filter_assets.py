#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import time

from ocean_lib.structures.file_objects import UrlFile


def test_search_and_filter_assets_by_tag(
    publisher_wallet, config, datatoken, publisher_ocean_instance
):
    tags = [
        ["test", "ganache", "best asset"],
        ["test", "ocean"],
        ["AI", "dataset", "testing"],
    ]

    for i in range(len(tags)):
        date_created = "2021-12-28T10:55:11Z"
        metadata = {
            "created": date_created,
            "updated": date_created,
            "description": "Branin dataset",
            "name": "Branin dataset",
            "type": "dataset",
            "author": "Trent",
            "license": "CC0: PublicDomain",
            "tags": tags[i],
        }

        url_file = UrlFile(
            url="https://raw.githubusercontent.com/trentmc/branin/main/branin.arff"
        )

        # Publish data asset
        asset = publisher_ocean_instance.assets.create(
            metadata, publisher_wallet, [url_file], deployed_datatokens=[datatoken]
        )
        print(f"Just published asset, with did={asset.did}")

    time.sleep(5)

    filtered_assets = publisher_ocean_instance.search_asset_by_tag(tag="test")

    # Make sure that the provided tag is valid.
    assert len(filtered_assets) > 0, "Assets not found with this tag."
    for asset in filtered_assets:
        assert "test" in asset.metadata["tags"]
