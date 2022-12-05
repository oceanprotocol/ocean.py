#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enum import IntEnum, IntFlag
from typing import List, Optional

from enforce_typing import enforce_types

from ocean_lib.models.datatoken import Datatoken
from ocean_lib.models.datatoken_enterprise import DatatokenEnterprise
from ocean_lib.web3_internal.constants import MAX_UINT256, ZERO_ADDRESS
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

    def create_datatoken(
        self,
        name: str,
        symbol: str,
        transaction_parameters: dict,
        template_index: Optional[int] = 1,
        minter: Optional[str] = None,
        fee_manager: Optional[str] = None,
        publish_market_order_fee_address: Optional[str] = None,
        publish_market_order_fee_token: Optional[str] = None,
        publish_market_order_fee_amount: Optional[int] = 0,
        bytess: Optional[List[bytes]] = None,
        datatoken_cap: Optional[int] = None,
        wrap_as_object: Optional[bool] = True,
    ) -> Datatoken:

        initial_list = self.getTokensList()

        local_values = locals().copy()

        from_address = (
            transaction_parameters["from"].address
            if isinstance(transaction_parameters["from"], object)
            else transaction_parameters["from"]
        )

        if minter is None:
            minter = from_address

        if fee_manager is None:
            fee_manager = from_address

        if publish_market_order_fee_address is None:
            publish_market_order_fee_address = from_address

        if publish_market_order_fee_token is None:
            publish_market_order_fee_token = ZERO_ADDRESS

        if bytess is None:
            bytess = [b""]

        if template_index == 2 and not datatoken_cap:
            raise Exception("Cap is needed for Datatoken Enterprise token deployment.")

        datatoken_cap = datatoken_cap if template_index == 2 else MAX_UINT256

        contract_call = self.contract.createERC20(
            template_index,
            [name, symbol],
            [
                ContractBase.to_checksum_address(minter),
                ContractBase.to_checksum_address(fee_manager),
                ContractBase.to_checksum_address(publish_market_order_fee_address),
                ContractBase.to_checksum_address(publish_market_order_fee_token),
            ],
            [datatoken_cap, publish_market_order_fee_amount],
            bytess,
            transaction_parameters,
        )

        if not wrap_as_object:
            return contract_call

        new_elements = [
            item for item in self.getTokensList() if item not in initial_list
        ]

        assert len(new_elements) == 1, "new data token has no address"

        return (
            Datatoken(self.config_dict, new_elements[0])
            if template_index == 1
            else DatatokenEnterprise(self.config_dict, new_elements[0])
        )
