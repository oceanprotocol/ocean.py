#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enum import IntEnum, IntFlag

from enforce_typing import enforce_types

from ocean_lib.models.datatoken import Datatoken
from ocean_lib.web3_internal.contract_base import ContractBase


class DataNFTPermissions(IntEnum):
    MANAGER = 0
    DEPLOY_DATATOKEN = 1
    UPDATE_METADATA = 2
    STORE = 3


class MetadataState(IntEnum):
    ACTIVE = 0
    END_OF_LIFE = 1
    DEPRECATED = 2
    REVOKED = 3
    TEMPORARILY_DISABLED = 4


class Flags(IntFlag):
    PLAIN = 0
    COMPRESSED = 1
    ENCRYPTED = 2

    def to_byte(self):
        return self.to_bytes(1, "big")


@enforce_types
class DataNFT(ContractBase):
    CONTRACT_NAME = "ERC721Template"

    def create_datatoken(self, datatoken_args, wallet) -> Datatoken:
        return datatoken_args.create_datatoken(self, wallet)

        # TODO
        # def ZERO ADDRESS
        # if publish_market_order_fee_address is None:
        #    publish_market_order_fee_address = from_address

        # def Ocean address
        # if publish_market_order_fee_token is None:
        #    publish_market_order_fee_token = ZERO_ADDRESS
