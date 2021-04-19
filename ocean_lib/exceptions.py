#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#


class OceanDIDAlreadyExist(Exception):
    """Raised when a requested DID is already published in OceanDB."""


class OceanEncryptAssetUrlsError(Exception):
    """Error invoking the encrypt endpoint."""


class InsufficientBalance(Exception):
    """The token balance is insufficient."""


class ContractNotFound(Exception):
    """Contract address is not found in the factory events."""


class AquariusError(Exception):
    """Error invoking an Aquarius metadata service endpoint."""


class VerifyTxFailed(Exception):
    """Transaction verification failed."""
