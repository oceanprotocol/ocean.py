#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enum import IntEnum, IntFlag
from typing import List, Optional, Union

from enforce_typing import enforce_types

from ocean_lib.models.datatoken import Datatoken
from ocean_lib.models.datatoken_enterprise import DatatokenEnterprise
from ocean_lib.structures.abi_tuples import MetadataProof
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

    @enforce_types
    def set_metadata_token_uri(
        self,
        metadata_state: int,
        metadata_decryptor_url: str,
        metadata_decryptor_address: bytes,
        flags: bytes,
        data: Union[str, bytes],
        data_hash: Union[str, bytes],
        token_id: int,
        token_uri: str,
        metadata_proofs: List[MetadataProof],
        transaction_parameters: dict,
    ) -> str:
        return self.contract.setMetaDataAndTokenURI(
            (
                metadata_state,
                metadata_decryptor_url,
                metadata_decryptor_address,
                flags,
                data,
                data_hash,
                token_id,
                token_uri,
                metadata_proofs,
            ),
            transaction_parameters,
        )

    @enforce_types
    def create_erc20(
        self,
        template_index: int,
        name: str,
        symbol: str,
        minter: str,
        fee_manager: str,
        publish_market_order_fee_address: str,
        publish_market_order_fee_token: str,
        publish_market_order_fee_amount: int,
        bytess: List[bytes],
        transaction_parameters: dict,
        datatoken_cap: Optional[int] = None,
    ) -> str:
        if template_index == 2 and not datatoken_cap:
            raise Exception("Cap is needed for Datatoken Enterprise token deployment.")
        datatoken_cap = datatoken_cap if template_index == 2 else MAX_UINT256
        return self.contract.createERC20(
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

    def create_datatoken(
        self,
        name: str,
        symbol: str,
        from_wallet,
        template_index: Optional[int] = 1,
        minter: Optional[str] = None,
        fee_manager: Optional[str] = None,
        publish_market_order_fee_address: Optional[str] = None,
        publish_market_order_fee_token: Optional[str] = None,
        publish_market_order_fee_amount: Optional[int] = 0,
        bytess: Optional[List[bytes]] = None,
        datatoken_cap: Optional[int] = None,
    ) -> Datatoken:
        initial_list = self.getTokensList()

        local_values = locals().copy()
        create_args = {
            lv_index: local_values[lv_index]
            for lv_index in [
                "template_index",
                "name",
                "symbol",
                "from_wallet",
                "minter",
                "fee_manager",
                "publish_market_order_fee_address",
                "publish_market_order_fee_token",
                "publish_market_order_fee_amount",
                "bytess",
            ]
        }

        for default_attribute in [
            "minter",
            "fee_manager",
            "publish_market_order_fee_address",
        ]:
            if create_args[default_attribute] is None:
                create_args[default_attribute] = from_wallet.address

        if publish_market_order_fee_token is None:
            create_args["publish_market_order_fee_token"] = ZERO_ADDRESS

        if bytess is None:
            create_args["bytess"] = [b""]

        if template_index == 2 and not datatoken_cap:
            raise Exception("Cap is needed for Datatoken Enterprise token deployment.")

        if template_index == 2:
            create_args["datatoken_cap"] = datatoken_cap

        create_args["transaction_parameters"] = {"from": create_args["from_wallet"]}
        create_args.pop("from_wallet")

        self.create_erc20(**create_args)

        new_elements = [
            item for item in self.getTokensList() if item not in initial_list
        ]

        assert len(new_elements) == 1, "new data token has no address"

        return (
            Datatoken(self.config_dict, new_elements[0])
            if template_index == 1
            else DatatokenEnterprise(self.config_dict, new_elements[0])
        )
