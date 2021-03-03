#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging

from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.event_filter import EventFilter
from ocean_lib.web3_internal.wallet import Wallet


class DTFactory(ContractBase):
    CONTRACT_NAME = "DTFactory"
    FIRST_BLOB = "https://example.com/dataset-1"

    def verify_data_token(self, dt_address):
        event = getattr(self.events, "TokenRegistered")
        filter_params = {"tokenAddress": dt_address}
        event_filter = event().createFilter(fromBlock=0, argument_filters=filter_params)
        logs = event_filter.get_all_entries()

        return logs and logs[0].args.tokenAddress == dt_address

    def get_token_registered_event(
        self, from_block, to_block, metadata_url=None, sender=None, token_address=None
    ):
        event = getattr(self.events, "TokenRegistered")
        filter_params = {}
        if token_address:
            filter_params["tokenAddress"] = token_address

        event_filter = event().createFilter(
            fromBlock=from_block, toBlock=to_block, argument_filters=filter_params
        )
        logs = event_filter.get_all_entries()
        if logs and token_address:
            return logs[0]

        for log in logs:
            if log.args.blob == metadata_url and sender == log.args.RegisteredBy:
                return log

        return None

    def get_token_minter(self, token_address):
        event = getattr(self.events, "TokenRegistered")
        # TODO: use the filter on tokenAddress when it is set as indexed in the contract event.
        filter_params = {}  # {'tokenAddress': token_address}
        event_filter = EventFilter(
            "TokenRegistered", event, filter_params, from_block=0, to_block="latest"
        )
        logs = event_filter.get_all_entries(max_tries=10)
        for log in logs:
            # assert log.args.tokenAddress == token_address
            if log.args.tokenAddress == token_address:
                return log.args.registeredBy

        return None

    def get_token_address(self, transaction_id: str) -> str:
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
