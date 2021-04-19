#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
"""Exceptions for ocean_lib.common """


#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0


class OceanInvalidContractAddress(Exception):
    """Raised when an invalid address is passed to the contract loader."""


class OceanDIDUnknownValueType(Exception):
    """Raised when a requested DID or a DID in the chain cannot be found."""


class OceanDIDAlreadyExist(Exception):
    """Raised when a requested DID is already published in OceanDB."""


class OceanInvalidMetadata(Exception):
    """Raised when some value in the metadata is invalid."""


class OceanInvalidServiceAgreementSignature(Exception):
    """Raised when the SLA signature is not valid."""


class OceanServiceAgreementExists(Exception):
    """Raised when the SLA already exists."""


class OceanInitializeServiceAgreementError(Exception):
    """Error on invoking purchase endpoint"""


class OceanEncryptAssetUrlsError(Exception):
    """Error invoking the encrypt endpoint"""


class OceanServiceConsumeError(Exception):
    """ Error invoking a purchase endpoint"""


class OceanInvalidAgreementTemplate(Exception):
    """ Error when agreement template is not valid or not approved"""
