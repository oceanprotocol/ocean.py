#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_lib.enforce_typing_shim import enforce_types_shim
from ocean_lib.models.data_token import DataToken
from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.wallet import Wallet


@enforce_types_shim
class DispenserContract(ContractBase):
    CONTRACT_NAME = "Dispenser"

    def status(self, dt_address: str) -> list:
        return self.contract_concise.status(dt_address)

    def status_dict(self, dt_address: str) -> dict:
        status_as_list = self.status(dt_address)
        return {
            "active": status_as_list[0],
            "owner": status_as_list[1],
            "minterApproved": status_as_list[2],
            "isTrueMinter": status_as_list[3],
            "maxTokens": status_as_list[4],
            "maxBalance": status_as_list[5],
            "balance": status_as_list[6],
        }

    def activate(
        self, dt_address: str, max_tokens: int, max_balance: int, from_wallet: Wallet
    ):
        return self.send_transaction(
            "activate", (dt_address, max_tokens, max_balance), from_wallet
        )

    def deactivate(self, dt_address: str, from_wallet: Wallet):
        return self.send_transaction("deactivate", (dt_address,), from_wallet)

    def make_minter(self, dt_address: str, from_wallet: Wallet):
        token = DataToken(dt_address)
        token.proposeMinter(self.address, from_wallet=from_wallet)
        return self.send_transaction("acceptMinter", (dt_address,), from_wallet)

    def cancel_minter(self, dt_address: str, from_wallet: Wallet):
        self.send_transaction("removeMinter", (dt_address,), from_wallet)
        token = DataToken(dt_address)
        return token.approveMinter(from_wallet)

    def dispense(self, dt_address: str, amount: int, from_wallet: Wallet):
        return self.send_transaction("dispense", (dt_address, amount), from_wallet)

    def owner_withdraw(self, dt_address: str, from_wallet: Wallet):
        return self.send_transaction("ownerWithdraw", (dt_address,), from_wallet)
