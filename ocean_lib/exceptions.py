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

class FailedToCreateDDO(Exception):
    """
    Failed to create DDO on-chain
    """
    pass

class FailedToUpdateDDO(Exception):
    """
    Failed to update DDO on-chain
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
