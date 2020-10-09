import json
import os
import time
from collections import namedtuple

from eth_utils import remove_0x_prefix
from web3 import Web3
from web3.utils.events import get_event_data

from ocean_lib.ocean.util import to_base_18, from_base_18
from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.event_filter import EventFilter
from ocean_lib.web3_internal.wallet import Wallet
from ocean_lib.web3_internal.web3_provider import Web3Provider
from ocean_utils.http_requests.requests_session import get_requests_session

from ocean_lib.data_provider.data_service_provider import DataServiceProvider

OrderValues = namedtuple(
    'OrderValues',
    ('consumer', 'amount', 'serviceId', 'startedAt', 'marketFeeCollector', 'marketFee')
)


class DataToken(ContractBase):
    CONTRACT_NAME = 'DataTokenTemplate'
    DEFAULT_CAP = 1000
    DEFAULT_CAP_BASE = to_base_18(DEFAULT_CAP)

    ORDER_STARTED_EVENT = 'OrderStarted'
    ORDER_FINISHED_EVENT = 'OrderFinished'

    OPF_FEE_PERCENTAGE = 0.001
    MAX_MARKET_FEE_PERCENTAGE = 0.001

    def get_event_signature(self, event_name):
        e = getattr(self.events, event_name)
        if not e:
            raise ValueError(f'Event {event_name} not found in {self.CONTRACT_NAME} contract.')

        abi = e().abi
        types = [param['type'] for param in abi['inputs']]
        sig_str = f'{event_name}({",".join(types)})'
        return Web3.sha3(text=sig_str).hex()

    def get_start_order_logs(self, web3, consumer_address, from_block=0, to_block='latest', from_all=False):
        topic0 = self.get_event_signature(self.ORDER_STARTED_EVENT)
        topic1 = f'0x000000000000000000000000{consumer_address[2:].lower()}'
        filter_params = {
            'fromBlock': from_block,
            'toBlock': to_block,
            'topics': [topic0, None, topic1],
        }
        if not from_all:
            filter_params['address'] = self.address

        e = getattr(self.events, self.ORDER_STARTED_EVENT)
        event_abi = e().abi
        logs = web3.eth.getLogs(filter_params)
        parsed_logs = []
        for l in logs:
            parsed_logs.append(get_event_data(event_abi, l))
        return parsed_logs

    def get_transfer_event(self, block_number, sender, receiver):
        event = getattr(self.events, 'Transfer')
        filter_params = {'from': sender, 'to': receiver}
        event_filter = EventFilter(
            'Transfer',
            event,
            filter_params,
            from_block=block_number-1,
            to_block=block_number+10
        )

        logs = event_filter.get_all_entries(max_tries=10)
        if not logs:
            return None

        if len(logs) > 1:
            raise AssertionError(f'Expected a single transfer event at '
                                 f'block {block_number}, but found {len(logs)} events.')

        return logs[0]

    def verify_transfer_tx(self, tx_id, sender, receiver):
        w3 = Web3Provider.get_web3()
        tx = w3.eth.getTransaction(tx_id)
        if not tx:
            raise AssertionError('Transaction is not found, or is not yet verified.')

        if tx['from'] != sender or tx['to'] != self.address:
            raise AssertionError(
                f'Sender and receiver in the transaction {tx_id} '
                f'do not match the expected consumer and contract addresses.'
            )

        _iter = 0
        while tx['blockNumber'] is None:
            time.sleep(0.1)
            tx = w3.eth.getTransaction(tx_id)
            _iter = _iter + 1
            if _iter > 100:
                break

        tx_receipt = self.get_tx_receipt(tx_id)
        if tx_receipt.status == 0:
            raise AssertionError(f'Transfer transaction failed.')

        logs = getattr(self.events, 'Transfer')().processReceipt(tx_receipt)
        transfer_event = logs[0] if logs else None
        # transfer_event = self.get_transfer_event(tx['blockNumber'], sender, receiver)
        if not transfer_event:
            raise AssertionError(f'Cannot find the event for the transfer transaction with tx id {tx_id}.')
        assert len(logs) == 1, \
            f'Multiple Transfer events in the same transaction !!! {logs}'

        if transfer_event.args['from'] != sender or transfer_event.args['to'] != receiver:
            raise AssertionError(f'The transfer event from/to do not match the expected values.')

        return tx, transfer_event

    def get_event_logs(self, event_name, filter_args=None, from_block=0, to_block='latest'):
        event = getattr(self.events, event_name)
        filter_params = filter_args or {}
        event_filter = EventFilter(
            event_name,
            event,
            filter_params,
            from_block=from_block,
            to_block=to_block
        )

        logs = event_filter.get_all_entries(max_tries=10)
        if not logs:
            return []

        return logs[0]

    def verify_order_tx(self, web3, tx_id, did, service_id, amount_base, sender):
        event = getattr(self.events, self.ORDER_STARTED_EVENT)
        tx_receipt = self.get_tx_receipt(tx_id)
        if tx_receipt.status == 0:
            raise AssertionError(f'order transaction failed.')

        receiver = self.contract_concise.minter()
        event_logs = event().processReceipt(tx_receipt)
        order_log = event_logs[0] if event_logs else None
        if not order_log:
            raise AssertionError(f'Cannot find the event for the order transaction with tx id {tx_id}.')
        assert len(event_logs) == 1, \
            f'Multiple order events in the same transaction !!! {event_logs}'

        asset_id = remove_0x_prefix(did).lower()
        assert asset_id == remove_0x_prefix(self.address).lower(), f'asset-id does not match the datatoken id.'
        if str(order_log.args.serviceId) != str(service_id):
            raise AssertionError(f'The asset id (DID) or service id in the event does '
                                 f'not match the requested asset. \n'
                                 f'requested: (did={did}, serviceId={service_id}\n'
                                 f'event: (serviceId={order_log.args.serviceId}')

        target_amount = amount_base - self.calculate_fee(amount_base, self.OPF_FEE_PERCENTAGE)
        if order_log.args.mrktFeeCollector and order_log.args.marketFee > 0:
            assert order_log.args.marketFee <= (self.calculate_fee(amount_base, self.MAX_MARKET_FEE_PERCENTAGE) + 5), \
                f'marketFee {order_log.args.marketFee} exceeds the expected maximum ' \
                f'of {self.calculate_fee(amount_base, self.MAX_MARKET_FEE_PERCENTAGE)} ' \
                f'based on feePercentage={self.MAX_MARKET_FEE_PERCENTAGE} .'
            target_amount = target_amount - order_log.args.marketFee

        # verify sender of the tx using the Tx record
        tx = web3.eth.getTransaction(tx_id)
        if tx['from'] != sender:
            raise AssertionError(f'sender of order transaction is not the same as the requesting account.')

        transfer_logs = self.events.Transfer().processReceipt(tx_receipt)
        receiver_to_transfers = {}
        for tr in transfer_logs:
            if tr.args.to not in receiver_to_transfers:
                receiver_to_transfers[tr.args.to] = []

            receiver_to_transfers[tr.args.to].append(tr)

        if receiver not in receiver_to_transfers:
            raise AssertionError(f'receiver {receiver} is not found in the transfer events.')
        transfers = sorted(receiver_to_transfers[receiver], key=lambda x: x.args.value)
        total = sum(tr.args.value for tr in transfers)
        if total < (target_amount - 5):
            raise ValueError(f'transferred value does meet the service cost: '
                             f'service.cost - fees={from_base_18(target_amount)}, '
                             f'transferred value={from_base_18(total)}')
        return tx, order_log, transfers[-1]

    def download(self, wallet: Wallet, tx_id: str, destination_folder: str):
        url = self.blob()
        download_url = (
            f'{url}?'
            f'consumerAddress={wallet.address}'
            f'&dataToken={self.address}'
            f'&transferTxId={tx_id}'
        )
        response = get_requests_session().get(download_url, stream=True)
        file_name = f'file-{self.address}'
        DataServiceProvider.write_file(response, destination_folder, file_name)
        return os.path.join(destination_folder, file_name)

    def token_balance(self, account: str):
        return from_base_18(self.balanceOf(account))

    def get_metadata_url(self):
        # grab the metadatastore URL from the DataToken contract (@token_address)
        url_object = json.loads(self.blob())
        assert url_object['t'] == 1, f'This datatoken does not appear to have a metadata store url.'
        return url_object['url']

    def get_simple_url(self):
        url_object = json.loads(self.blob())
        assert url_object['t'] == 0, f'This datatoken does not appear to have a direct consume url.'
        return url_object['url']

    # ============================================================
    # Token transactions using amount of tokens as a float instead of int
    # amount of tokens will be converted to the base value before sending
    # the transaction
    def approve_tokens(self, spender: str, value: float, from_wallet: Wallet, wait: bool=False):
        txid = self.approve(spender, to_base_18(value), from_wallet)
        if wait:
            self.get_tx_receipt(txid)

        return txid

    def mint_tokens(self, to_account: str, value: float, from_wallet: Wallet):
        return self.mint(to_account, to_base_18(value), from_wallet)

    def transfer_tokens(self, to: str, value: float, from_wallet: Wallet):
        return self.transfer(to, to_base_18(value), from_wallet)

    ################
    # Helpers
    @staticmethod
    def get_max_fee_percentage():
        return DataToken.OPF_FEE_PERCENTAGE + DataToken.MAX_MARKET_FEE_PERCENTAGE

    @staticmethod
    def calculate_max_fee(amount):
        return DataToken.calculate_fee(amount, DataToken.get_max_fee_percentage())

    @staticmethod
    def calculate_fee(amount, percentage):
        return int(amount * to_base_18(percentage) / to_base_18(1.0))

    # ============================================================
    # reflect DataToken Solidity methods
    def blob(self) -> str:
        return self.contract_concise.blob()

    def symbol(self) -> str:
        return self.contract_concise.symbol()

    def decimals(self) -> str:
        return self.contract_concise.decimals()

    def allowance(self, owner_address: str, spender_address: str) -> str:
        return self.contract_concise.allowance(owner_address, spender_address)

    def balanceOf(self, account: str) -> int:
        return self.contract_concise.balanceOf(account)

    def mint(self, to_account: str, value_base: int, from_wallet: Wallet) -> str:
        return self.send_transaction('mint', (to_account, value_base), from_wallet)

    def approve(self, spender: str, value_base: int, from_wallet: Wallet) -> str:
        return self.send_transaction('approve', (spender, value_base), from_wallet)

    def transfer(self, to: str, value_base: int, from_wallet: Wallet) -> str:
        return self.send_transaction('transfer', (to, value_base), from_wallet)

    def proposeMinter(self, new_minter, from_wallet) -> str:
        return self.send_transaction('proposeMinter', (new_minter, ), from_wallet)

    def approveMinter(self, from_wallet) -> str:
        return self.send_transaction('approveMinter', (), from_wallet)

    def startOrder(self, consumer: str, amount: int, serviceId: int, mrktFeeCollector: str, from_wallet: Wallet):
        return self.send_transaction(
            'startOrder',
            (consumer, amount, serviceId, mrktFeeCollector),
            from_wallet
        )

    def finishOrder(self, orderTxId: str, consumer: str, amount: int,
                    serviceId: int, from_wallet: Wallet):
        return self.send_transaction(
            'finishOrder',
            (orderTxId, consumer, amount, serviceId),
            from_wallet
        )
