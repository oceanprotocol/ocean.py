#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import List, Optional, Union

from enforce_typing import enforce_types
from web3.exceptions import BadFunctionCallOutput

from ocean_lib.models.data_nft import DataNFT
from ocean_lib.models.datatoken import Datatoken
from ocean_lib.models.erc721_token_factory_base import ERC721TokenFactoryBase
from ocean_lib.models.fixed_rate_exchange import FixedRateExchange
from ocean_lib.structures.abi_tuples import MetadataProof, OrderData
from ocean_lib.web3_internal.constants import MAX_UINT256
from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.wallet import Wallet


class DataNFTFactoryContract(ERC721TokenFactoryBase):
    CONTRACT_NAME = "ERC721Factory"
    EVENT_NFT_CREATED = "NFTCreated"
    EVENT_TOKEN_CREATED = "TokenCreated"
    EVENT_TEMPLATE721_ADDED = "Template721Added"
    EVENT_TEMPLATE20_ADDED = "Template20Added"
    EVENT_NEW_POOL = "NewPool"
    EVENT_NEW_FIXED_RATE = "NewFixedRate"
    EVENT_DISPENSER_CREATED = "DispenserCreated"
    EVENT_TRANSFER = "Transfer"

    @property
    def event_NFTCreated(self):
        return self.events.NFTCreated()

    @property
    def event_TokenCreated(self):
        return self.events.TokenCreated()

    @property
    def event_Template721Added(self):
        return self.events.Template721Added()

    @property
    def event_Template20Added(self):
        return self.events.Template20Added()

    @property
    def event_NewPool(self):
        return self.events.NewPool()

    @property
    def event_NewFixedRate(self):
        return self.events.NewFixedRate()

    @property
    def event_DispenserCreated(self):
        return self.events.DispenserCreated()

    @property
    def event_Transfer(self):
        return self.events.Transfer()

    @enforce_types
    def verify_nft(self, nft_address: str) -> bool:
        """Checks that a token was registered."""
        data_nft_contract = DataNFT(self.web3, nft_address)
        try:
            data_nft_contract.get_id()
            return True
        except BadFunctionCallOutput:
            return False

    @enforce_types
    def deploy_erc721_contract(
        self,
        name: str,
        symbol: str,
        template_index: int,
        additional_metadata_updater: str,
        additional_datatoken_deployer: str,
        token_uri: str,
        transferable: bool,
        owner: str,
        from_wallet: Wallet,
    ):
        return self.send_transaction(
            "deployERC721Contract",
            (
                name,
                symbol,
                template_index,
                ContractBase.to_checksum_address(additional_metadata_updater),
                ContractBase.to_checksum_address(additional_datatoken_deployer),
                token_uri,
                transferable,
                ContractBase.to_checksum_address(owner),
            ),
            from_wallet,
        )

    @enforce_types
    def get_current_nft_count(self) -> int:
        return self.contract.caller.getCurrentNFTCount()

    @enforce_types
    def get_nft_template(self, template_index: int) -> list:
        return self.contract.caller.getNFTTemplate(template_index)

    @enforce_types
    def get_current_nft_template_count(self) -> int:
        return self.contract.caller.getCurrentNFTTemplateCount()

    @enforce_types
    def is_contract(self, account_address: str) -> bool:
        return self.contract.caller.isContract(
            ContractBase.to_checksum_address(account_address)
        )

    @enforce_types
    def get_current_token_count(self) -> int:
        return self.contract.caller.getCurrentTokenCount()

    @enforce_types
    def get_token_template(self, index: int) -> list:
        return self.contract.caller.getTokenTemplate(index)

    @enforce_types
    def get_current_template_count(self) -> int:
        return self.contract.caller.getCurrentTemplateCount()

    @enforce_types
    def template_count(self) -> int:
        return self.contract.caller.templateCount()

    @enforce_types
    def start_multiple_token_order(
        self, orders: List[OrderData], from_wallet: Wallet
    ) -> str:
        """An order contains the following keys:

        - tokenAddress, str
        - consumer, str
        - serviceIndex, int
        - providerFeeAddress, str
        - providerFeeToken, str
        - providerFeeAmount (in Wei), int
        - providerData, bytes
        - v, int
        - r, bytes
        - s, bytes
        """
        for order in orders:
            order._replace(
                token_address=ContractBase.to_checksum_address(order.token_address)
            )
            order._replace(consumer=ContractBase.to_checksum_address(order.consumer))
            provider_fees = list(order.provider_fees)
            provider_fees[0] = ContractBase.to_checksum_address(order.provider_fees[0])
            provider_fees[1] = ContractBase.to_checksum_address(order.provider_fees[1])
            order._replace(provider_fees=tuple(provider_fees))
            consume_fees = list(order.consume_fees)
            consume_fees[0] = ContractBase.to_checksum_address(order.consume_fees[0])
            consume_fees[1] = ContractBase.to_checksum_address(order.consume_fees[1])
            order._replace(consume_fees=tuple(consume_fees))
        return self.send_transaction("startMultipleTokenOrder", (orders,), from_wallet)

    @enforce_types
    def create_nft_with_erc20(
        self,
        nft_name: str,
        nft_symbol: str,
        nft_template: int,
        nft_token_uri: str,
        nft_transferable: bool,
        nft_owner: str,
        datatoken_template: int,
        datatoken_name: str,
        datatoken_symbol: str,
        datatoken_minter: str,
        datatoken_fee_manager: str,
        datatoken_publish_market_order_fee_address: str,
        datatoken_publish_market_order_fee_token: str,
        datatoken_publish_market_order_fee_amount: int,
        datatoken_bytess: List[bytes],
        from_wallet: Wallet,
        datatoken_cap: Optional[int] = None,
    ) -> str:
        if datatoken_template == 2 and not datatoken_cap:
            raise Exception("Cap is needed for Datatoken Enterprise token deployment.")
        datatoken_cap = datatoken_cap if datatoken_template == 2 else MAX_UINT256
        return self.send_transaction(
            "createNftWithErc20",
            (
                (
                    nft_name,
                    nft_symbol,
                    nft_template,
                    nft_token_uri,
                    nft_transferable,
                    ContractBase.to_checksum_address(nft_owner),
                ),
                (
                    datatoken_template,
                    [datatoken_name, datatoken_symbol],
                    [
                        ContractBase.to_checksum_address(datatoken_minter),
                        ContractBase.to_checksum_address(datatoken_fee_manager),
                        ContractBase.to_checksum_address(
                            datatoken_publish_market_order_fee_address
                        ),
                        ContractBase.to_checksum_address(
                            datatoken_publish_market_order_fee_token
                        ),
                    ],
                    [datatoken_cap, datatoken_publish_market_order_fee_amount],
                    datatoken_bytess,
                ),
            ),
            from_wallet,
        )

    @enforce_types
    def create_nft_erc20_with_fixed_rate(
        self,
        nft_name: str,
        nft_symbol: str,
        nft_template: int,
        nft_token_uri: str,
        nft_transferable: bool,
        nft_owner: str,
        datatoken_template: int,
        datatoken_name: str,
        datatoken_symbol: str,
        datatoken_minter: str,
        datatoken_fee_manager: str,
        datatoken_publish_market_order_fee_address: str,
        datatoken_publish_market_order_fee_token: str,
        datatoken_publish_market_order_fee_amount: int,
        datatoken_bytess: List[bytes],
        fixed_price_address: str,
        fixed_price_base_token: str,
        fixed_price_owner: str,
        fixed_price_publish_market_swap_fee_collector: str,
        fixed_price_allowed_swapper: str,
        fixed_price_base_token_decimals: int,
        fixed_price_datatoken_decimals: int,
        fixed_price_rate: int,
        fixed_price_publish_market_swap_fee_amount: int,
        fixed_price_with_mint: int,
        from_wallet: Wallet,
        datatoken_cap: Optional[int] = None,
    ) -> str:
        if datatoken_template == 2 and not datatoken_cap:
            raise Exception("Cap is needed for Datatoken Enterprise token deployment.")
        datatoken_cap = datatoken_cap if datatoken_template == 2 else MAX_UINT256
        return self.send_transaction(
            "createNftWithErc20WithFixedRate",
            (
                (
                    nft_name,
                    nft_symbol,
                    nft_template,
                    nft_token_uri,
                    nft_transferable,
                    ContractBase.to_checksum_address(nft_owner),
                ),
                (
                    datatoken_template,
                    [datatoken_name, datatoken_symbol],
                    [
                        ContractBase.to_checksum_address(datatoken_minter),
                        ContractBase.to_checksum_address(datatoken_fee_manager),
                        ContractBase.to_checksum_address(
                            datatoken_publish_market_order_fee_address
                        ),
                        ContractBase.to_checksum_address(
                            datatoken_publish_market_order_fee_token
                        ),
                    ],
                    [datatoken_cap, datatoken_publish_market_order_fee_amount],
                    datatoken_bytess,
                ),
                (
                    ContractBase.to_checksum_address(fixed_price_address),
                    [
                        ContractBase.to_checksum_address(fixed_price_base_token),
                        ContractBase.to_checksum_address(fixed_price_owner),
                        ContractBase.to_checksum_address(
                            fixed_price_publish_market_swap_fee_collector
                        ),
                        ContractBase.to_checksum_address(fixed_price_allowed_swapper),
                    ],
                    [
                        fixed_price_base_token_decimals,
                        fixed_price_datatoken_decimals,
                        fixed_price_rate,
                        fixed_price_publish_market_swap_fee_amount,
                        fixed_price_with_mint,
                    ],
                ),
            ),
            from_wallet,
        )

    @enforce_types
    def create_nft_erc20_with_dispenser(
        self,
        nft_name: str,
        nft_symbol: str,
        nft_template: int,
        nft_token_uri: str,
        nft_transferable: bool,
        nft_owner: str,
        datatoken_template: int,
        datatoken_name: str,
        datatoken_symbol: str,
        datatoken_minter: str,
        datatoken_fee_manager: str,
        datatoken_publish_market_order_fee_address: str,
        datatoken_publish_market_order_fee_token: str,
        datatoken_publish_market_order_fee_amount: int,
        datatoken_bytess: List[bytes],
        dispenser_address: str,
        dispenser_max_tokens: int,
        dispenser_max_balance: int,
        dispenser_with_mint: bool,
        dispenser_allowed_swapper: str,
        from_wallet: Wallet,
        datatoken_cap: Optional[int] = None,
    ) -> str:
        if datatoken_template == 2 and not datatoken_cap:
            raise Exception("Cap is needed for Datatoken Enterprise token deployment.")
        datatoken_cap = datatoken_cap if datatoken_template == 2 else MAX_UINT256
        return self.send_transaction(
            "createNftWithErc20WithDispenser",
            (
                (
                    nft_name,
                    nft_symbol,
                    nft_template,
                    nft_token_uri,
                    nft_transferable,
                    ContractBase.to_checksum_address(nft_owner),
                ),
                (
                    datatoken_template,
                    [datatoken_name, datatoken_symbol],
                    [
                        ContractBase.to_checksum_address(datatoken_minter),
                        ContractBase.to_checksum_address(datatoken_fee_manager),
                        ContractBase.to_checksum_address(
                            datatoken_publish_market_order_fee_address
                        ),
                        ContractBase.to_checksum_address(
                            datatoken_publish_market_order_fee_token
                        ),
                    ],
                    [datatoken_cap, datatoken_publish_market_order_fee_amount],
                    datatoken_bytess,
                ),
                (
                    ContractBase.to_checksum_address(dispenser_address),
                    dispenser_max_tokens,
                    dispenser_max_balance,
                    dispenser_with_mint,
                    ContractBase.to_checksum_address(dispenser_allowed_swapper),
                ),
            ),
            from_wallet,
        )

    @enforce_types
    def create_nft_with_metadata(
        self,
        nft_name: str,
        nft_symbol: str,
        nft_template: int,
        nft_token_uri: str,
        nft_transferable: bool,
        nft_owner: str,
        metadata_state: int,
        metadata_decryptor_url: str,
        metadata_decryptor_address: str,
        metadata_flags: bytes,
        metadata_data: Union[str, bytes],
        metadata_data_hash: Union[str, bytes],
        metadata_proofs: List[MetadataProof],
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "createNftWithMetaData",
            (
                (
                    nft_name,
                    nft_symbol,
                    nft_template,
                    nft_token_uri,
                    nft_transferable,
                    ContractBase.to_checksum_address(nft_owner),
                ),
                (
                    metadata_state,
                    metadata_decryptor_url,
                    ContractBase.to_checksum_address(metadata_decryptor_address),
                    metadata_flags,
                    metadata_data,
                    metadata_data_hash,
                    metadata_proofs,
                ),
            ),
            from_wallet,
        )

    @enforce_types
    def search_exchange_by_datatoken(
        self,
        fixed_rate_exchange: FixedRateExchange,
        datatoken: str,
        exchange_owner: Optional[str] = None,
    ) -> list:
        datatoken_contract = Datatoken(self.web3, datatoken)
        exchange_addresses_and_ids = datatoken_contract.get_fixed_rates()
        return (
            exchange_addresses_and_ids
            if exchange_owner is None
            else [
                exchange_address_and_id
                for exchange_address_and_id in exchange_addresses_and_ids
                if fixed_rate_exchange.get_exchange(exchange_address_and_id[1])[0]
                == exchange_owner
            ]
        )

    @enforce_types
    def get_token_address(self, tx_id: Union[str, bytes]):
        tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_id)
        registered_event = self.get_event_log(
            event_name=DataNFTFactoryContract.EVENT_NFT_CREATED,
            from_block=tx_receipt.blockNumber,
            to_block=self.web3.eth.block_number,
            filters=None,
        )

        return registered_event[0].args.newTokenAddress

    @enforce_types
    def check_datatoken(self, datatoken_address: str) -> bool:
        return self.contract.caller.erc20List(datatoken_address)

    @enforce_types
    def check_nft(self, nft_address: str) -> bool:
        return self.contract.caller.erc721List(nft_address) == nft_address
