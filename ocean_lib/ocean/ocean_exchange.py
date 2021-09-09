#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

from typing import Optional, Tuple, Union, List

from enforce_typing import enforce_types
from web3.datastructures import AttributeDict

from ocean_lib.config import Config
from ocean_lib.exceptions import InsufficientBalance, VerifyTxFailed
from ocean_lib.models.data_token import DataToken
from ocean_lib.models.fixed_rate_exchange import FixedRateExchange
from ocean_lib.web3_internal.currency import pretty_ether_and_wei
from ocean_lib.web3_internal.wallet import Wallet
from web3.exceptions import ValidationError
from web3.logs import DISCARD
from web3.main import Web3


class OceanExchange:
    @enforce_types
    def __init__(
        self,
        web3: Web3,
        ocean_token_address: str,
        exchange_address: str,
        config: Config,
    ) -> None:
        """Initialises OceanExchange object."""
        self.ocean_address = ocean_token_address
        self._exchange_address = exchange_address
        self._config = config
        self._web3 = web3

    @enforce_types
    def _exchange_contract(self) -> FixedRateExchange:
        return FixedRateExchange(self._web3, self._exchange_address)

    @enforce_types
    def get_quote(self, amount: int, exchange_id: Union[str, bytes]) -> int:
        exchange = self._exchange_contract()
        return exchange.get_base_token_quote(exchange_id, amount)

    @enforce_types
    def get_exchange_id_fallback_dt_and_owner(
        self, exchange_id: Union[bytes, str], exchange_owner: str, data_token: str
    ) -> Tuple[FixedRateExchange, bytes]:
        exchange = self._exchange_contract()

        if exchange_id:
            return exchange, exchange_id

        assert (
            exchange_owner and data_token
        ), "exchange_owner and data_token are required when exchange_id is not given."

        return (
            exchange,
            exchange.generateExchangeId(self.ocean_address, data_token, exchange_owner),
        )

    @enforce_types
    def search_exchange_by_data_token(self, data_token: str) -> List[AttributeDict]:
        fre = self._exchange_contract()
        events = fre.events
        exchange_event = getattr(events, "ExchangeCreated")
        filter_args = {"dataToken": data_token}
        logs = fre.getLogs(
            exchange_event,
            argument_filters=filter_args,
            fromBlock=0,
            toBlock=self._web3.eth.block_number,
        )
        return logs

    @enforce_types
    def buy_at_fixed_rate(
        self,
        amount: int,
        wallet: Wallet,
        max_OCEAN_amount: int,
        exchange_id: Optional[Union[bytes, str]] = "",
        data_token: Optional[str] = "",
        exchange_owner: Optional[str] = "",
    ) -> bool:

        exchange, exchange_id = self.get_exchange_id_fallback_dt_and_owner(
            exchange_id, exchange_owner, data_token
        )

        # Figure out the amount of ocean tokens to approve before triggering the exchange function to do the swap
        ocean_amount = exchange.get_base_token_quote(exchange_id, amount)
        ocean_token = DataToken(self._web3, self.ocean_address)
        ocean_ticker = ocean_token.symbol()
        if ocean_amount > max_OCEAN_amount:
            raise ValidationError(
                f"Buying {pretty_ether_and_wei(amount, 'DataTokens')} requires {pretty_ether_and_wei(ocean_amount, ocean_ticker)} "
                f"tokens which exceeds the max_OCEAN_amount {pretty_ether_and_wei(max_OCEAN_amount, ocean_ticker)}."
            )
        if ocean_token.balanceOf(wallet.address) < ocean_amount:
            raise InsufficientBalance(
                f"Insufficient funds for buying {pretty_ether_and_wei(amount, 'DataTokens')}!"
            )
        if ocean_token.allowance(wallet.address, self._exchange_address) < ocean_amount:
            tx_id = ocean_token.approve(self._exchange_address, ocean_amount, wallet)
            tx_receipt = ocean_token.get_tx_receipt(self._web3, tx_id)
            if not tx_receipt or tx_receipt.status != 1:
                raise VerifyTxFailed(
                    f"Approve OCEAN tokens failed, exchange address was {self._exchange_address} and tx id was {tx_id}!"
                )
        tx_id = exchange.buy_data_token(
            exchange_id, data_token_amount=amount, from_wallet=wallet
        )
        return bool(exchange.get_tx_receipt(self._web3, tx_id).status)

    @enforce_types
    def create(self, data_token: str, exchange_rate: int, wallet: Wallet) -> str:
        assert exchange_rate > 0, "Invalid exchange rate, must be > 0"
        exchange = self._exchange_contract()
        tx_id = exchange.create(
            self.ocean_address, data_token, exchange_rate, from_wallet=wallet
        )
        # get tx receipt
        tx_receipt = exchange.get_tx_receipt(self._web3, tx_id)
        # get event log from receipt
        logs = exchange.contract.events.ExchangeCreated().processReceipt(
            tx_receipt, errors=DISCARD
        )
        if not logs:
            raise VerifyTxFailed(
                f"Create new datatoken exchange failed, transaction receipt for tx {tx_id} is not found."
            )

        exchange_id = logs[0].args.exchangeId  # get from event log args
        # compare exchange_id to generateExchangeId() value
        assert exchange_id == exchange.generateExchangeId(
            self.ocean_address, data_token, wallet.address
        )

        return exchange_id

    @enforce_types
    def setRate(
        self,
        new_rate: int,
        wallet: Wallet,
        exchange_id: Optional[Union[bytes, str]] = "",
        data_token: Optional[str] = "",
        exchange_owner: Optional[str] = "",
    ) -> bool:
        assert new_rate > 0, "Invalid exchange rate, must be > 0"

        exchange, exchange_id = self.get_exchange_id_fallback_dt_and_owner(
            exchange_id, exchange_owner, data_token
        )

        tx_id = exchange.setRate(exchange_id, new_rate, from_wallet=wallet)
        # get tx receipt
        tx_receipt = exchange.get_tx_receipt(self._web3, tx_id)
        # get event log from receipt
        logs = exchange.contract.events.ExchangeRateChanged().processReceipt(
            tx_receipt, errors=DISCARD
        )
        if not logs:
            raise VerifyTxFailed(
                f"Set rate for exchange_id {exchange_id} failed, transaction receipt for tx {tx_id} is not found."
            )

        return True
