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


class ProviderError(Exception):
    """
    Generic provider error
    """


class AquariusError(Exception):
    """
    Generic aquarius error
    """

