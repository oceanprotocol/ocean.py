class ContractNotFound(Exception):
    """
    Contract address is not found
    in the factory events
    """


class DDOError(Exception):
    """
    Generic DDO Error
    """

    pass


class InsufficientBalance(Exception):
    """
    The token balance is not sufficient
    """

    pass


class AssetsError(Exception):
    """
    Generic Assets Error
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
    Generic Transaction Revert Error
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
