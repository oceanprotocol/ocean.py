#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json
import os
import sys

from PIL import Image


def get_input(local=False):
    if local:
        print("Reading local file lena.png.")

        return "lena.png"

    dids = os.getenv("DIDS", None)

    if not dids:
        print("No DIDs found in environment. Aborting.")
        return

    dids = json.loads(dids)

    for did in dids:
        filename = f"data/inputs/{did}/0"  # 0 for metadata service
        print(f"Reading asset file {filename}.")

        return filename


def run_grayscale(local=False):
    filename = get_input(local)
    if not filename:
        print("Could not retrieve filename.")
        return

    img = Image.open(filename).convert("L")

    result_filename = "output/grayscale.png" if local else "/data/outputs/grayscale.png"
    img.save(result_filename)


if __name__ == "__main__":
    local = len(sys.argv) == 2 and sys.argv[1] == "local"
    run_grayscale(local)
