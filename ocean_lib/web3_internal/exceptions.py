class OceanKeeperContractsNotFound(Exception):
    """Raised when is not possible to find the keeper contracts abi."""


class OceanDIDNotFound(Exception):
    """Raised when a requested DID or a DID in the chain cannot be found."""


class OceanInvalidTransaction(Exception):
    """Raised when an on-chain transaction fail."""
