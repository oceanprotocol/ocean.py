#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enforce_typing import enforce_types
from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.wallet import Wallet


@enforce_types
class ERC721Token(ContractBase):
    CONTRACT_NAME = "ERC721Template"

    def initialize(
        self,
        name: str,
        symbol: str,
        metadata_address: str,
        erc20_factory_address: str,
        data: bytes,
        flags: bytes,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "initialize",
            (name, symbol, metadata_address, erc20_factory_address, data, flags),
            from_wallet,
        )

    def update_metadata(self, flags: bytes, data: bytes) -> str:
        return self.contract.caller.updateMetadata(flags, data)

    def create_erc20(
        self,
        name: str,
        symbol: str,
        cap: int,
        template_index: int,
        minter_address: str,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "createERC20", (name, symbol, template_index, minter_address), from_wallet
        )

    def add_manager(self, manager_address: str, from_wallet: Wallet) -> None:
        return self.send_transaction("addManager", (manager_address), from_wallet)

    def remove_manager(self, manager_address: str, from_wallet: Wallet) -> None:
        return self.send_transaction("removeManager", (manager_address), from_wallet)

    def execute_call(
        self, operation: int, to: str, value: int, data: bytes, from_wallet: Wallet
    ) -> None:
        return self.send_transaction("executeCall", (operation, to, value), from_wallet)

    def set_new_data(self, key: bytes, value: bytes, from_wallet: Wallet) -> None:
        return self.send_transaction("executeCall", (key, value), from_wallet)

    def set_data_erc20(self, key: bytes, value: bytes, from_wallet: Wallet) -> None:
        return self.send_transaction("setDataERC20", (key, value), from_wallet)

    def set_data_v3(
        self,
        datatoken: str,
        value: bytes,
        flags: bytes,
        data: bytes,
        from_wallet: Wallet,
    ) -> None:
        return self.send_transaction(
            "setDataV3", (datatoken, value, flags, data), from_wallet
        )

    def wrap_v3_dt(self, datatoken: str, new_minter: str, from_wallet: Wallet) -> None:
        return self.send_transaction("wrapV3DT", (datatoken, new_minter), from_wallet)

    def mint_v3_dt(
        self, datatoken: str, to_address: str, value: int, from_wallet: Wallet
    ) -> None:
        return self.send_transaction(
            "mintV3DT", (datatoken, to_address, value), from_wallet
        )

    def add_v3_minter(self, new_minter_address: str, from_wallet: Wallet) -> None:
        return self.send_transaction("addV3Minter", (new_minter_address), from_wallet)

    def remove_v3_minter(self, minter_address: str, from_wallet: Wallet) -> None:
        return self.send_transaction("removeV3Minter", (minter_address), from_wallet)

    def transfer_from(
        self, from_address: str, to_address: str, token_id: int, from_wallet: Wallet
    ) -> None:
        return self.send_transaction(
            "transferFrom", (from_address, to_address, token_id), from_wallet
        )

    def name(self) -> str:
        return self.contract.caller.name()

    def symbol(self) -> str:
        return self.contract.caller.symbol()

    def is_initialized(self) -> bool:
        return self.contract.caller.isInitialized()

    def clean_permissions(self) -> None:
        return self.contract.caller.cleanPermissions()

    def get_address_length(self, array: list[str]) -> int:
        return self.contract.caller.getAddressLength(array)
