class ContractNotFound(Exception):
    """
    Datatoken address is not found
    in the datatoken factory events
    """

    pass


class DDOError(Exception):
    """
    Failed to encrypt ddo files
    """

    pass


class InsufficientBalance(Exception):
    """
    The datatoken balance balance is not sufficient
    """

    pass


class AssetsError(Exception):
    """
    The datatoken balance balance is not sufficient
    """

    pass


class BPoolError(Exception):
    """
    Generic Balancer Pool Error
    """

    pass


class ExchangeError(Exception):
    """
    Generic Ocean Exchange Error
    """

    pass


class TransactionReverted(Exception):
    """
    Generic transaction revert error
    """

    pass


class ProviderError(Exception):
    """
    Generic provider error
    """

    pass


class AquariusError(Exception):
    """
    Generic aquarius error
    """

    pass
