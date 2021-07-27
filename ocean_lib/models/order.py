#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""
Defines namedtuple `Order`
"""
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
