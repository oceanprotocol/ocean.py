#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from dataclasses import dataclass

from enforce_typing.decorator import enforce_types


@dataclass
@enforce_types
class Integer:
    value: int
