#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import List

from enforce_typing import enforce_types


@enforce_types
class File(object):
    def __init__(self, url: str, method: str) -> None:
        self.url = url
        self.method = method
        self.type = "url"


@enforce_types
class FileObjects(object):
    def __init__(self, files: List[File]):
        self.files = files
