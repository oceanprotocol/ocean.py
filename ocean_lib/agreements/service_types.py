#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
"""Agreements module."""


class ServiceTypesIndices:
    DEFAULT_METADATA_INDEX = 0
    DEFAULT_PROVENANCE_INDEX = 1
    DEFAULT_AUTHORIZATION_INDEX = 2
    DEFAULT_ACCESS_INDEX = 3
    DEFAULT_COMPUTING_INDEX = 4


class ServiceTypes:
    """Types of Service allowed in ocean protocol DDO services for V4."""

    ASSET_ACCESS = "access"
    CLOUD_COMPUTE = "compute"
    AUTHORIZATION = "wss"


class ServiceTypesNames:
    DEFAULT_ACCESS_NAME = "Download service"
    DEFAULT_COMPUTE_NAME = "Compute service"
