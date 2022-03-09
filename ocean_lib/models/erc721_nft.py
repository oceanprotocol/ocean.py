#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enum import IntEnum
from typing import List

from enforce_typing import enforce_types

from ocean_lib.models.erc20_enterprise import ERC20Enterprise
from ocean_lib.models.erc20_token import ERC20Token
from ocean_lib.structures.abi_tuples import (
    MetadataProof,
)
from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.wallet import Wallet


class ERC721Permissions(IntEnum):
    MANAGER = 0
    DEPLOY_ERC20 = 1
    UPDATE_METADATA = 2
    STORE = 3


@enforce_types
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

    def set_metadata_state(self, metadata_state: int, from_wallet: Wallet):
        return self.send_transaction("setMetaDataState", (metadata_state,), from_wallet)

    def set_metadata(
        self,
        metadata_state: int,
        metadata_decryptor_url: str,
        metadata_decryptor_address: str,
        flags: bytes,
        data: bytes,
        data_hash: bytes,
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

    def set_metadata_token_uri(
        self,
        metadata_state: int,
        metadata_decryptor_url: str,
        metadata_decryptor_address: str,
        flags: bytes,
        data: bytes,
        data_hash: bytes,
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

    def get_metadata(self) -> tuple:
        return self.contract.caller.getMetaData()

    def create_erc20(
        self,
        template_index: int,
        datatoken_name: str,
        datatoken_symbol: str,
        datatoken_minter: str,
        datatoken_fee_manager: str,
        datatoken_publishing_market_address: str,
        fee_token_address: str,
        datatoken_cap: int,
        publishing_market_fee_amount: int,
        bytess: List[bytes],
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "createERC20",
            (
                template_index,
                [datatoken_name, datatoken_symbol],
                [
                    datatoken_minter,
                    datatoken_fee_manager,
                    datatoken_publishing_market_address,
                    fee_token_address,
                ],
                [datatoken_cap, publishing_market_fee_amount],
                bytess,
            ),
            from_wallet,
        )

    def add_to_create_erc20_list(
        self, allowed_address: str, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "addToCreateERC20List", (allowed_address,), from_wallet
        )

    def add_to_725_store_list(self, allowed_address: str, from_wallet: Wallet) -> str:
        return self.send_transaction(
            "addTo725StoreList", (allowed_address,), from_wallet
        )

    def add_to_metadata_list(self, allowed_address: str, from_wallet: Wallet) -> str:
        return self.send_transaction(
            "addToMetadataList", (allowed_address,), from_wallet
        )

    def add_manager(self, manager_address: str, from_wallet: Wallet) -> str:
        return self.send_transaction("addManager", (manager_address,), from_wallet)

    def remove_manager(self, manager_address: str, from_wallet: Wallet) -> str:
        return self.send_transaction("removeManager", (manager_address,), from_wallet)

    def execute_call(
        self, operation: int, to: str, value: int, data: bytes, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "executeCall", (operation, to, value, data), from_wallet
        )

    def set_new_data(self, key: bytes, value: bytes, from_wallet: Wallet) -> str:
        return self.send_transaction("setNewData", (key, value), from_wallet)

    def set_data_erc20(self, key: bytes, value: bytes, from_wallet: Wallet) -> str:
        return self.send_transaction("setDataERC20", (key, value), from_wallet)

    def set_data_v3(self, datatoken: str, value: bytes, from_wallet: Wallet) -> str:
        return self.send_transaction("setDataV3", (datatoken, value), from_wallet)

    def get_data(self, key: bytes) -> bytes:
        return self.contract.caller.getData(key)

    def token_uri(self, token_id: int) -> str:
        return self.contract.caller.tokenURI(token_id)

    def wrap_v3_dt(self, datatoken: str, new_minter: str, from_wallet: Wallet) -> str:
        return self.send_transaction("wrapV3DT", (datatoken, new_minter), from_wallet)

    def mint_v3_dt(
        self, datatoken: str, to_address: str, value: int, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "mintV3DT", (datatoken, to_address, value), from_wallet
        )

    def add_v3_minter(self, new_minter_address: str, from_wallet: Wallet) -> str:
        return self.send_transaction("addV3Minter", (new_minter_address,), from_wallet)

    def remove_v3_minter(self, minter_address: str, from_wallet: Wallet) -> str:
        return self.send_transaction("removeV3Minter", (minter_address,), from_wallet)

    def transfer_from(
        self, from_address: str, to_address: str, token_id: int, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "transferFrom", (from_address, to_address, token_id), from_wallet
        )

    def safe_transfer_from(
        self, from_address: str, to_address: str, token_id: int, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "safeTransferFrom", (from_address, to_address, token_id), from_wallet
        )

    def withdraw(self, from_wallet: Wallet):
        return self.send_transaction("withdrawETH", (), from_wallet)

    def token_name(self) -> str:
        return self.contract.caller.name()

    def symbol(self) -> str:
        return self.contract.caller.symbol()

    def is_initialized(self) -> bool:
        return self.contract.caller.isInitialized()

    def clean_permissions(self, from_wallet: Wallet) -> str:
        return self.send_transaction("cleanPermissions", (), from_wallet)

    def get_address_length(self, array: List[str]) -> int:
        return self.contract.caller.getAddressLength(array)

    def get_permissions(self, user: str) -> list:
        return self.contract.caller.getPermissions(user)

    def balance_of(self, account: str) -> int:
        return self.contract.caller.balanceOf(account)

    def owner_of(self, token_id: int) -> str:
        return self.contract.caller.ownerOf(token_id)

    def get_tokens_list(self) -> list:
        return self.contract.caller.getTokensList()

    def is_deployed(self, datatoken: str) -> bool:
        return self.contract.caller.isDeployed(datatoken)

    def is_erc20_deployer(self, account: str) -> bool:
        return self.contract.caller.isERC20Deployer(account)

    def set_token_uri(
        self, token_id: int, new_token_uri: str, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "setTokenURI", (token_id, new_token_uri), from_wallet
        )

    def create_datatoken(
        self,
        template_index: int,
        datatoken_name: str,
        datatoken_symbol: str,
        datatoken_minter: str,
        datatoken_fee_manager: str,
        datatoken_publishing_market_address: str,
        fee_token_address: str,
        datatoken_cap: int,
        publishing_market_fee_amount: int,
        bytess: List[bytes],
        from_wallet: Wallet,
    ) -> ERC20Token:
        initial_list = self.get_tokens_list()

        tx_id = self.create_erc20(
            template_index=template_index,
            datatoken_name=datatoken_name,
            datatoken_symbol=datatoken_symbol,
            datatoken_minter=datatoken_minter,
            datatoken_fee_manager=datatoken_fee_manager,
            datatoken_publishing_market_address=datatoken_publishing_market_address,
            fee_token_address=fee_token_address,
            datatoken_cap=datatoken_cap,
            publishing_market_fee_amount=publishing_market_fee_amount,
            bytess=bytess,
            from_wallet=from_wallet,
        )
        self.web3.eth.wait_for_transaction_receipt(tx_id)

        new_elements = [
            item for item in self.get_tokens_list() if item not in initial_list
        ]

        assert len(new_elements) == 1, "new data token has no address"

        return (
            ERC20Token(self.web3, new_elements[0])
            if template_index == 1
            else ERC20Enterprise(self.web3, new_elements[0])
        )
