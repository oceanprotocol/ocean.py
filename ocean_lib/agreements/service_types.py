#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
"""Agreements module."""


class ServiceTypes:
    """Types of Service allowed in ocean protocol DDO services for V4."""

    ASSET_ACCESS = "access"
    CLOUD_COMPUTE = "compute"
    AUTHORIZATION = "wss"


class ServiceTypesNames:
    DEFAULT_ACCESS_NAME = "Download service"
    DEFAULT_COMPUTE_NAME = "Compute service"
