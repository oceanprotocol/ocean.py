class InvalidDatatokenContract(Exception):
    """
    does not seem to be a valid DataToken contract
    """

    pass


class InvalidDatatokenMinter(Exception):
    """
    Minter of datatoken is not the same as
    the publisher address
    """

    pass


class DatatokenNotFound(Exception):
    """
    Datatoken address is not found
    in the datatoken factory events
    """

    pass


class FailedToEncryptDDOFiles(Exception):
    """
    Failed to encrypt ddo files
    """

    pass


class InsufficientDatatokenBalance(Exception):
    """
    The datatoken balance balance is not sufficient
    """

    pass


class FailedToOrder(Exception):
    """
    The datatoken balance balance is not sufficient
    """

    pass


class FailedToCreateNewPool(Exception):
    """
    Failed to setup and create new ocean-datatoken pool
    """

    pass


class FailedToCreateExchange(Exception):
    """
    Failed create new exchange
    """

    pass


class FailedToSetExchangeRate(Exception):
    """
    Failed set exchange rate
    """

    pass


class AmountOfOceanTokensExceedsMaxLimit(Exception):
    """
    Buying X datatokens requires Y OCEAN which exceeds the max OCEAN limit.
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
