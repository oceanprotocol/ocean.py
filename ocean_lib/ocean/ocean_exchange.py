from ocean_lib.config import Config
from ocean_lib.models.data_token import DataToken
from ocean_lib.models.dtfactory import DTFactory
from ocean_lib.models.fixed_rate_exchange import FixedRateExchange
from ocean_lib.ocean.util import from_base_18
from ocean_lib.ocean.util import get_dtfactory_address, to_base_18
from ocean_lib.web3_internal.wallet import Wallet


class OceanExchange:
    def __init__(self, ocean_token_address: str, exchange_address: str, config: Config):
        self.ocean_address = ocean_token_address
        self._exchange_address = exchange_address
        self._config = config

    def _exchange_contract(self):
        return FixedRateExchange(self._exchange_address)

    def get_quote(self, amount: float, exchange_id: str):
        exchange = self._exchange_contract()
        amount_base = to_base_18(amount)
        ocean_amount_base = exchange.get_base_token_quote(
            exchange_id, amount_base
        )
        return from_base_18(ocean_amount_base)

    def buy_at_fixed_rate(
            self, amount: float, wallet: Wallet,
            max_OCEAN_amount: float, exchange_id: str='', data_token: str='', exchange_owner: str='') -> bool:

        exchange = self._exchange_contract()
        if not exchange_id:
            assert exchange_owner and data_token, f'exchange_owner and data_token are required when exchange_id is not given.'
            exchange_id = exchange.generateExchangeId(self.ocean_address, data_token, exchange_owner)

        amount_base = to_base_18(amount)
        max_OCEAN_amount_base = to_base_18(max_OCEAN_amount)

        # Figure out the amount of ocean tokens to approve before triggering the exchange function to do the swap
        ocean_amount_base = exchange.get_base_token_quote(exchange_id, amount_base)
        if ocean_amount_base > max_OCEAN_amount_base:
            raise AssertionError(f'Buying {amount} datatokens requires {from_base_18(ocean_amount_base)} OCEAN '
                                 f'tokens which exceeds the max_OCEAN_amount {max_OCEAN_amount}.')
        ocean_token = DataToken(self.ocean_address)
        ocean_token.get_tx_receipt(ocean_token.approve(self._exchange_address, ocean_amount_base, wallet))
        tx_id = exchange.buy_data_token( exchange_id, data_token_amount=amount_base, from_wallet=wallet)
        return bool(exchange.get_tx_receipt(tx_id).status)

    def create(self, data_token: str, exchange_rate: float, wallet: Wallet) -> str:
        assert exchange_rate > 0, 'Invalid exchange rate, must be > 0'
        exchange = self._exchange_contract()
        exchange_rate_base = to_base_18(exchange_rate)
        tx_id = exchange.create(self.ocean_address, data_token, exchange_rate_base, from_wallet=wallet)
        # get tx receipt
        tx_receipt = exchange.get_tx_receipt(tx_id)
        # get event log from receipt
        logs = exchange.contract.events.ExchangeCreated().processReceipt(tx_receipt)
        if not logs:
            raise AssertionError(
                f'Create new datatoken exchange failed, transaction receipt for tx {tx_id} is not found.')

        exchange_id = logs[0].args.exchangeId  # get from event log args
        # compare exchange_id to generateExchangeId() value
        assert exchange_id == exchange.generateExchangeId(self.ocean_address, data_token, wallet.address)

        return exchange_id
