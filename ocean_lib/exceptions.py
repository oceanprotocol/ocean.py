#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#


class ContractNotFound(Exception):
    """
    Contract address is not found
    in the factory events
    """


class DDOError(Exception):
    """
    Generic DDO Error
    """


class InsufficientBalance(Exception):
    """
    The token balance is not sufficient
    """


class AssetsError(Exception):
    """
    Generic Assets Error
    """


class BPoolError(Exception):
    """
    Generic Balancer Pool Error
    """


class ExchangeError(Exception):
    """
    Generic Ocean Exchange Error
    """


class TransactionReverted(Exception):
    """
    Generic Transaction Revert Error
    """


class InvalidURL(Exception):
    """
    Raised when a URL can not be
    parsed in DataServiceProvider.
    """


class AquariusError(Exception):
    """
    Generic aquarius error
    """
