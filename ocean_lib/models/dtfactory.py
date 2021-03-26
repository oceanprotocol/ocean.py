#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging

from ocean_lib.enforce_typing_shim import enforce_types_shim
from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.wallet import Wallet


@enforce_types_shim
class DTFactory(ContractBase):
    CONTRACT_NAME = "DTFactory"
    FIRST_BLOB = "https://example.com/dataset-1"

    def verify_data_token(self, dt_address):
        """Checks that a token was registered."""
        event = getattr(self.events, "TokenRegistered")
        filter_params = {"tokenAddress": dt_address}
        event_filter = event().createFilter(fromBlock=0, argument_filters=filter_params)
        logs = event_filter.get_all_entries()

        return logs and logs[0].args.tokenAddress == dt_address

    def get_token_registered_event(self, from_block, to_block, token_address):
        """Retrieves event log of token registration."""
        event = getattr(self.events, "TokenRegistered")
        filter_params = {"tokenAddress": token_address}

        event_filter = event().createFilter(
            fromBlock=from_block, toBlock=to_block, argument_filters=filter_params
        )
        logs = event_filter.get_all_entries()

        return logs[0] if logs else None

    def get_token_minter(self, token_address):
        """Retrieves token minter.

        This function will be deprecated in the next major release.
        It's only kept for backwards compatibility."""
        from ocean_lib.models.data_token import DataToken  # isort:skip

        dt = DataToken(address=token_address)

        return dt.contract_concise.minter()

    def get_token_address(self, transaction_id: str) -> str:
        """Gets token address using transaction id."""
        tx_receipt = self.get_tx_receipt(transaction_id)
        if not tx_receipt:
            logging.warning(
                f"Cannot get the transaction receipt for tx {transaction_id}."
            )
            return ""

        logs = getattr(self.events, "TokenRegistered")().processReceipt(tx_receipt)
        if not logs:
            logging.warning(f"No logs were found for tx {transaction_id}.")
            return ""

        return logs[0].args.tokenAddress

    # ============================================================
    # reflect DataToken Solidity methods
    def createToken(
        self, blob: str, name: str, symbol: str, cap: int, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "createToken", (blob, name, symbol, cap), from_wallet
        )
