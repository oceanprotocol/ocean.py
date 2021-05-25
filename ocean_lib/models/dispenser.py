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

    def status(self, dt_address: str) -> dict:
        status_as_list = self.contract_concise.status(dt_address)
        return {
            "active": status_as_list[0],
            "owner": status_as_list[1],
            "minterApproved": status_as_list[2],
            "isTrueMinter": status_as_list[3],
            "maxTokens": status_as_list[4],
            "maxBalance": status_as_list[5],
            "balance": status_as_list[6],
        }

    def is_active(self, dt_address: str) -> bool:
        return self.status(dt_address).get("active", False)

    def owner(self, dt_address: str) -> str:
        return self.status(dt_address).get("owner", None)

    def is_minter_approved(self, dt_address: str) -> bool:
        return self.status(dt_address).get("minterApproved", False)

    def is_true_minter(self, dt_address: str) -> bool:
        return self.status(dt_address).get("isTrueMinter", False)

    def max_tokens(self, dt_address: str) -> int:
        return self.status(dt_address).get("maxTokens", 0)

    def max_balance(self, dt_address: str) -> int:
        return self.status(dt_address).get("maxBalance", 0)

    def balance(self, dt_address: str) -> int:
        return self.status(dt_address).get("balance", 0)

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

    # TODO: is dispensable
