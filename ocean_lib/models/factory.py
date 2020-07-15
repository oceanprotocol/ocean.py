import logging

from ocean_lib.models.datatokencontract import DataTokenContract
from ocean_lib.web3_internal import ContractBase
from ocean_lib.web3_internal.contract_handler import ContractHandler
from ocean_lib.web3_internal.event_filter import EventFilter
from ocean_lib.web3_internal.web3_provider import Web3Provider


class FactoryContract(ContractBase):
    CONTRACT_NAME = 'Factory'
    CAP = 1400000000
    FIRST_BLOB = 'https://example.com/dataset-1'

    def deploy(self, abi_path, minter_address):
        if not abi_path:
            abi_path = ContractHandler.artifacts_path

        assert abi_path, f'abi_path is required, got {abi_path}'

        w3 = Web3Provider.get_web3()
        w3.eth.defaultAccount = w3.toChecksumAddress(minter_address)
        print(f'default account: {w3.eth.defaultAccount}')
        factory_json = ContractHandler.read_abi_from_file(
            FactoryContract.CONTRACT_NAME,
            abi_path
        )
        dt_contract_json = ContractHandler.read_abi_from_file(
            DataTokenContract.CONTRACT_NAME,
            abi_path
        )

        # First deploy the DataTokenTemplate contract
        dt_contract = w3.eth.contract(abi=dt_contract_json['abi'], bytecode=dt_contract_json['bytecode'])
        tx_hash = dt_contract.constructor(
            'Template Contract', 'TEMPLATE', minter_address, FactoryContract.CAP, FactoryContract.FIRST_BLOB
        ).transact()
        dt_template_address = self.get_tx_receipt(tx_hash, timeout=60).contractAddress

        factory_contract = w3.eth.contract(abi=factory_json['abi'], bytecode=factory_json['bytecode'])
        tx_hash = factory_contract.constructor(
            dt_template_address
        ).transact({'from': minter_address})

        return self.get_tx_receipt(tx_hash, timeout=60).contractAddress

    def create_data_token(self, account, metadata_url):
        tx_hash = self.send_transaction(
            'createToken',
            (metadata_url,),
            transact={'from': account.address,
                      'passphrase': account.password,
                      'account_key': account.key},
        )
        tx_receipt = self.get_tx_receipt(tx_hash)
        if not tx_receipt:
            logging.warning(f'Cannot get the transaction receipt for tx {tx_hash}.')
            return None

        logs = getattr(self.events, 'TokenRegistered')().processReceipt(tx_receipt)
        if not logs:
            logging.warning(f'No logs where found for tx {tx_hash}.')
            return None

        return DataTokenContract(logs[0].args.tokenAddress)

    def get_token_registered_event(self, block_number, metadata_url, sender):
        event = getattr(self.events, 'TokenRegistered')
        filter_params = {}
        event_filter = event().createFilter(
            fromBlock=block_number,
            toBlock=block_number,
            argument_filters=filter_params
        )
        logs = event_filter.get_all_entries()
        for log in logs:
            if log.args.blob == metadata_url and sender == log.args.RegisteredBy:
                return log

        return None

    def get_token_minter(self, token_address):
        event = getattr(self.events, 'TokenRegistered')
        # TODO: use the filter on tokenAddress when it is set as indexed in the contract event.
        filter_params = {}  # {'tokenAddress': token_address}
        event_filter = EventFilter(
            'TokenRegistered',
            event,
            filter_params,
            from_block=0,
            to_block='latest'
        )
        logs = event_filter.get_all_entries(max_tries=10)
        for log in logs:
            # assert log.args.tokenAddress == token_address
            if log.args.tokenAddress == token_address:
                return log.args.registeredBy

        return None
