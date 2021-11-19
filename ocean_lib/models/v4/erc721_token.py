#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enum import IntEnum
from typing import List

from enforce_typing import enforce_types

from ocean_lib.models.v4.models_structures import ErcCreateData
from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.wallet import Wallet


class ERC721Permissions(IntEnum):
    MANAGER = 0
    DEPLOY_ERC20 = 1
    UPDATE_METADATA = 2
    STORE = 3


@enforce_types
class ERC721Token(ContractBase):
    CONTRACT_NAME = "ERC721Template"

    EVENT_TOKEN_CREATED = "TokenCreated"
    EVENT_METADATA_CREATED = "MetadataCreated"
    EVENT_METADATA_UPDATED = "MetadataUpdated"

    @property
    def event_MetadataCreated(self):
        return self.events.MetadataCreated()

    @property
    def event_MetadataUpdated(self):
        return self.events.MetadataUpdated()

    @property
    def event_TokenCreated(self):
        return self.events.TokenCreated()

    def initialize(
        self,
        owner: str,
        name: str,
        symbol: str,
        token_factory_address: str,
        additional_erc20_deployer: str,
        base_uri: str,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "initialize",
            (
                owner,
                name,
                symbol,
                token_factory_address,
                additional_erc20_deployer,
                base_uri,
            ),
            from_wallet,
        )

    def set_metadata(
        self,
        metadata_state: int,
        metadata_decryptor_url: str,
        metadata_decryptor_address: str,
        flags: bytes,
        data: bytes,
        data_hash: bytes,
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
            ),
            from_wallet,
        )

    def get_metadata(self) -> tuple:
        return self.contract.caller.getMetaData()

    def create_erc20(self, erc_create_data: ErcCreateData, from_wallet: Wallet) -> str:
        return self.send_transaction(
            "createERC20",
            (
                erc_create_data.template_index,
                erc_create_data.strings,
                erc_create_data.addresses,
                erc_create_data.uints,
                erc_create_data.bytess,
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

    def is_deployed(self, data_token: str) -> bool:
        return self.contract.caller.isDeployed(data_token)

    def set_token_uri(
        self, token_id: int, new_base_uri: str, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "setTokenURI", (token_id, new_base_uri), from_wallet
        )
