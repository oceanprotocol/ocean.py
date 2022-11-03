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


class DataNFTFactoryContract(ERC721TokenFactoryBase):
    CONTRACT_NAME = "ERC721Factory"

    @enforce_types
    def verify_nft(self, nft_address: str) -> bool:
        """Checks that a token was registered."""
        data_nft_contract = DataNFT(self.config_dict, nft_address)
        try:
            data_nft_contract.getId()
            return True
        except BadFunctionCallOutput:
            return False

    @enforce_types
    def start_multiple_token_order(
        self, orders: List[OrderData], transaction_parameters: dict
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

        return self.contract.startMultipleTokenOrder(orders, transaction_parameters)

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
        transaction_parameters: dict,
        datatoken_cap: Optional[int] = None,
    ) -> str:
        if datatoken_template == 2 and not datatoken_cap:
            raise Exception("Cap is needed for Datatoken Enterprise token deployment.")
        datatoken_cap = datatoken_cap if datatoken_template == 2 else MAX_UINT256
        return self.contract.createNftWithErc20(
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
            transaction_parameters,
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
        transaction_parameters: dict,
        datatoken_cap: Optional[int] = None,
    ) -> str:
        if datatoken_template == 2 and not datatoken_cap:
            raise Exception("Cap is needed for Datatoken Enterprise token deployment.")
        datatoken_cap = datatoken_cap if datatoken_template == 2 else MAX_UINT256
        return self.contract.createNftWithErc20WithFixedRate(
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
            transaction_parameters,
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
        transaction_parameters: dict,
        datatoken_cap: Optional[int] = None,
    ) -> str:
        if datatoken_template == 2 and not datatoken_cap:
            raise Exception("Cap is needed for Datatoken Enterprise token deployment.")
        datatoken_cap = datatoken_cap if datatoken_template == 2 else MAX_UINT256
        return self.contract.createNftWithErc20WithDispenser(
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
            transaction_parameters,
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
        metadata_decryptor_address: bytes,
        metadata_flags: bytes,
        metadata_data: Union[str, bytes],
        metadata_data_hash: Union[str, bytes],
        metadata_proofs: List[MetadataProof],
        transaction_parameters: dict,
    ) -> str:
        return self.contract.createNftWithMetaData(
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
                metadata_decryptor_address,
                metadata_flags,
                metadata_data,
                metadata_data_hash,
                metadata_proofs,
            ),
            transaction_parameters,
        )

    @enforce_types
    def search_exchange_by_datatoken(
        self,
        fixed_rate_exchange: FixedRateExchange,
        datatoken: str,
        exchange_owner: Optional[str] = None,
    ) -> list:
        datatoken_contract = Datatoken(self.config_dict, datatoken)
        exchange_addresses_and_ids = datatoken_contract.getFixedRates()
        return (
            exchange_addresses_and_ids
            if exchange_owner is None
            else [
                exchange_address_and_id
                for exchange_address_and_id in exchange_addresses_and_ids
                if fixed_rate_exchange.getExchange(exchange_address_and_id[1])[0]
                == exchange_owner
            ]
        )

    @enforce_types
    def get_token_address(self, receipt):
        return receipt.events["NFTCreated"]["newTokenAddress"]

    @enforce_types
    def check_datatoken(self, datatoken_address: str) -> bool:
        return self.contract.erc20List(datatoken_address)

    @enforce_types
    def check_nft(self, nft_address: str) -> bool:
        return self.contract.erc721List(nft_address) == nft_address
