#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#


class ConsumableCodes:
    OK = 0
    ASSET_DISABLED = 1
    CONNECTIVITY_FAIL = 2
    CREDENTIAL_NOT_IN_ALLOW_LIST = 3
    CREDENTIAL_IN_DENY_LIST = 4


class UnsupportedCredential(Exception):
    pass


class MalformedCredential(Exception):
    pass
