#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enum import IntEnum
from typing import List, Union

from enforce_typing import enforce_types

from ocean_lib.models.erc20_enterprise import ERC20Enterprise
from ocean_lib.models.erc20_token import ERC20Token
from ocean_lib.structures.abi_tuples import MetadataProof
from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.wallet import Wallet


class ERC721Permissions(IntEnum):
    MANAGER = 0
    DEPLOY_ERC20 = 1
    UPDATE_METADATA = 2
    STORE = 3


class ERC721NFT(ContractBase):
    CONTRACT_NAME = "ERC721Template"

    EVENT_TOKEN_CREATED = "TokenCreated"
    EVENT_METADATA_CREATED = "MetadataCreated"
    EVENT_METADATA_UPDATED = "MetadataUpdated"
    EVENT_METADATA_VALIDATED = "MetadataValidated"
    EVENT_TOKEN_URI_UPDATED = "TokenURIUpdate"

    @property
    def event_MetadataCreated(self):
        return self.events.MetadataCreated()

    @property
    def event_MetadataUpdated(self):
        return self.events.MetadataUpdated()

    @property
    def event_MetadataValidated(self):
        return self.events.MetadataValidated()

    @property
    def event_TokenCreated(self):
        return self.events.TokenCreated()

    @property
    def event_TokenURIUpdate(self):
        return self.events.TokenURIUpdate()

    @enforce_types
    def set_metadata_state(self, metadata_state: int, from_wallet: Wallet):
        return self.send_transaction("setMetaDataState", (metadata_state,), from_wallet)

    @enforce_types
    def set_metadata(
        self,
        metadata_state: int,
        metadata_decryptor_url: str,
        metadata_decryptor_address: str,
        flags: bytes,
        data: Union[str, bytes],
        data_hash: Union[str, bytes],
        metadata_proofs: List[MetadataProof],
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "setMetaData",
            (
                metadata_state,
                metadata_decryptor_url,
                metadata_decryptor_address,
                flags,
                data,
                data_hash,
                metadata_proofs,
            ),
            from_wallet,
        )

    @enforce_types
    def set_metadata_token_uri(
        self,
        metadata_state: int,
        metadata_decryptor_url: str,
        metadata_decryptor_address: str,
        flags: bytes,
        data: Union[str, bytes],
        data_hash: Union[str, bytes],
        token_id: int,
        token_uri: str,
        metadata_proofs: List[MetadataProof],
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "setMetaDataAndTokenURI",
            (
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
            ),
            from_wallet,
        )

    @enforce_types
    def get_metadata(self) -> tuple:
        return self.contract.caller.getMetaData()

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
        cap: int,
        publish_market_order_fee_amount: int,
        bytess: List[bytes],
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "createERC20",
            (
                template_index,
                [name, symbol],
                [
                    minter,
                    fee_manager,
                    publish_market_order_fee_address,
                    publish_market_order_fee_token,
                ],
                [cap, publish_market_order_fee_amount],
                bytess,
            ),
            from_wallet,
        )

    @enforce_types
    def add_to_create_erc20_list(
        self, allowed_address: str, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "addToCreateERC20List", (allowed_address,), from_wallet
        )

    @enforce_types
    def add_to_725_store_list(self, allowed_address: str, from_wallet: Wallet) -> str:
        return self.send_transaction(
            "addTo725StoreList", (allowed_address,), from_wallet
        )

    @enforce_types
    def add_to_metadata_list(self, allowed_address: str, from_wallet: Wallet) -> str:
        return self.send_transaction(
            "addToMetadataList", (allowed_address,), from_wallet
        )

    @enforce_types
    def add_manager(self, manager_address: str, from_wallet: Wallet) -> str:
        return self.send_transaction("addManager", (manager_address,), from_wallet)

    @enforce_types
    def remove_manager(self, manager_address: str, from_wallet: Wallet) -> str:
        return self.send_transaction("removeManager", (manager_address,), from_wallet)

    @enforce_types
    def execute_call(
        self, operation: int, to: str, value: int, data: str, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "executeCall", (operation, to, value, data), from_wallet
        )

    @enforce_types
    def set_new_data(self, key: bytes, value: str, from_wallet: Wallet) -> str:
        return self.send_transaction("setNewData", (key, value), from_wallet)

    @enforce_types
    def set_data_erc20(self, key: bytes, value: str, from_wallet: Wallet) -> str:
        return self.send_transaction("setDataERC20", (key, value), from_wallet)

    @enforce_types
    def get_data(self, key: bytes) -> bytes:
        return self.contract.caller.getData(key)

    @enforce_types
    def token_uri(self, token_id: int) -> str:
        return self.contract.caller.tokenURI(token_id)

    @enforce_types
    def transfer_from(
        self, from_address: str, to_address: str, token_id: int, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "transferFrom", (from_address, to_address, token_id), from_wallet
        )

    @enforce_types
    def safe_transfer_from(
        self, from_address: str, to_address: str, token_id: int, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "safeTransferFrom", (from_address, to_address, token_id), from_wallet
        )

    @enforce_types
    def withdraw(self, from_wallet: Wallet):
        return self.send_transaction("withdrawETH", (), from_wallet)

    @enforce_types
    def token_name(self) -> str:
        return self.contract.caller.name()

    @enforce_types
    def symbol(self) -> str:
        return self.contract.caller.symbol()

    @enforce_types
    def is_initialized(self) -> bool:
        return self.contract.caller.isInitialized()

    @enforce_types
    def clean_permissions(self, from_wallet: Wallet) -> str:
        return self.send_transaction("cleanPermissions", (), from_wallet)

    @enforce_types
    def get_address_length(self, array: List[str]) -> int:
        return self.contract.caller.getAddressLength(array)

    @enforce_types
    def get_id(self) -> int:
        return self.contract.caller.getId()

    @enforce_types
    def get_permissions(self, user: str) -> list:
        return self.contract.caller.getPermissions(user)

    @enforce_types
    def balance_of(self, account: str) -> int:
        return self.contract.caller.balanceOf(account)

    @enforce_types
    def owner_of(self, token_id: int) -> str:
        return self.contract.caller.ownerOf(token_id)

    @enforce_types
    def get_tokens_list(self) -> list:
        return self.contract.caller.getTokensList()

    @enforce_types
    def is_deployed(self, datatoken: str) -> bool:
        return self.contract.caller.isDeployed(datatoken)

    @enforce_types
    def is_erc20_deployer(self, account: str) -> bool:
        return self.contract.caller.isERC20Deployer(account)

    @enforce_types
    def set_token_uri(
        self, token_id: int, new_token_uri: str, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "setTokenURI", (token_id, new_token_uri), from_wallet
        )

    @enforce_types
    def create_datatoken(
        self,
        template_index: int,
        name: str,
        symbol: str,
        minter: str,
        fee_manager: str,
        publish_market_order_fee_address: str,
        publish_market_order_fee_token: str,
        cap: int,
        publish_market_order_fee_amount: int,
        bytess: List[bytes],
        from_wallet: Wallet,
    ) -> ERC20Token:
        initial_list = self.get_tokens_list()

        self.create_erc20(
            template_index=template_index,
            name=name,
            symbol=symbol,
            minter=minter,
            fee_manager=fee_manager,
            publish_market_order_fee_address=publish_market_order_fee_address,
            publish_market_order_fee_token=publish_market_order_fee_token,
            cap=cap,
            publish_market_order_fee_amount=publish_market_order_fee_amount,
            bytess=bytess,
            from_wallet=from_wallet,
        )

        new_elements = [
            item for item in self.get_tokens_list() if item not in initial_list
        ]

        assert len(new_elements) == 1, "new data token has no address"

        return (
            ERC20Token(self.web3, new_elements[0])
            if template_index == 1
            else ERC20Enterprise(self.web3, new_elements[0])
        )
