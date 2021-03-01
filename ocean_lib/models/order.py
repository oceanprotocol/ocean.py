#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from collections import namedtuple

Order = namedtuple(
    "Order",
    (
        "datatoken",
        "amount",
        "timestamp",
        "transactionId",
        "did",
        "payer",
        "consumer",
        "serviceId",
        "serviceType",
    ),
)
