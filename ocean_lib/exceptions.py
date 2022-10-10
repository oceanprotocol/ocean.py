#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#


class OceanEncryptAssetUrlsError(Exception):
    """Error invoking the encrypt endpoint."""


class InsufficientBalance(Exception):
    """The token balance is insufficient."""


class AquariusError(Exception):
    """Error invoking an Aquarius metadata service endpoint."""


class VerifyTxFailed(Exception):
    """Transaction verification failed."""


class TransactionFailed(Exception):
    """Transaction has failed."""


class DataProviderException(Exception):
    """Exception from Provider endpoints."""
