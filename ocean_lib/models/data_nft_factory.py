#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import List, Optional, Union

from enforce_typing import enforce_types
from web3.exceptions import BadFunctionCallOutput

from ocean_lib.models.data_nft import DataNFT
from ocean_lib.models.datatoken import Datatoken
from ocean_lib.models.datatoken_enterprise import DatatokenEnterprise
from ocean_lib.models.erc721_token_factory_base import ERC721TokenFactoryBase
from ocean_lib.models.fixed_rate_exchange import FixedRateExchange, OneExchange
from ocean_lib.ocean.util import get_address_of_type
from ocean_lib.structures.abi_tuples import MetadataProof, OrderData
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

    def create(self, data_nft_args, tx_dict):
        return data_nft_args.deploy_contract(self.config_dict, tx_dict)

    @enforce_types
    def start_multiple_token_order(self, orders: List[OrderData], tx_dict: dict) -> str:
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

        return self.contract.startMultipleTokenOrder(orders, tx_dict)

    @enforce_types
    def create_with_erc20(
        self,
        data_nft_args,
        datatoken_args,
        wallet=None,
    ) -> str:
        receipt = self.contract.createNftWithErc20(
            (
                data_nft_args.name,
                data_nft_args.symbol,
                data_nft_args.template_index,
                data_nft_args.uri,
                data_nft_args.transferable,
                ContractBase.to_checksum_address(data_nft_args.owner or wallet.address),
            ),
            (
                datatoken_args.template_index,
                [datatoken_args.name, datatoken_args.symbol],
                [
                    ContractBase.to_checksum_address(
                        datatoken_args.minter or wallet.address
                    ),
                    ContractBase.to_checksum_address(
                        datatoken_args.fee_manager or wallet.address
                    ),
                    ContractBase.to_checksum_address(
                        datatoken_args.publish_market_order_fees.address
                    ),
                    ContractBase.to_checksum_address(
                        datatoken_args.publish_market_order_fees.token
                    ),
                ],
                [datatoken_args.cap, datatoken_args.publish_market_order_fees.amount],
                datatoken_args.bytess,
            ),
            {"from": wallet},
        )

        registered_nft_event = receipt.events["NFTCreated"]
        data_nft_address = registered_nft_event["newTokenAddress"]
        data_nft_token = DataNFT(self.config_dict, data_nft_address)

        registered_token_event = receipt.events["TokenCreated"]
        datatoken_address = registered_token_event["newTokenAddress"]
        datatoken = (
            Datatoken(self.config_dict, datatoken_address)
            if datatoken_args.template_index == 1
            else DatatokenEnterprise(self.config_dict, datatoken_address)
        )

        return data_nft_token, datatoken

    @enforce_types
    def create_with_erc20_and_fixed_rate(
        self,
        data_nft_args,
        datatoken_args,
        fixed_price_base_token: str,
        fixed_price_owner: str,
        fixed_price_publish_market_swap_fee_collector: str,
        fixed_price_allowed_swapper: str,
        fixed_price_base_token_decimals: int,
        fixed_price_datatoken_decimals: int,
        fixed_price_rate: Union[int, str],
        fixed_price_publish_market_swap_fee_amount: Union[int, str],
        fixed_price_with_mint: Union[int, str],
        wallet=None,
    ) -> str:
        fixed_price_address = get_address_of_type(self.config_dict, "FixedPrice")

        receipt = self.contract.createNftWithErc20WithFixedRate(
            (
                data_nft_args.name,
                data_nft_args.symbol,
                data_nft_args.template_index,
                data_nft_args.uri,
                data_nft_args.transferable,
                ContractBase.to_checksum_address(data_nft_args.owner or wallet.address),
            ),
            (
                datatoken_args.template_index,
                [datatoken_args.name, datatoken_args.symbol],
                [
                    ContractBase.to_checksum_address(
                        datatoken_args.minter or wallet.address
                    ),
                    ContractBase.to_checksum_address(
                        datatoken_args.fee_manager or wallet.address
                    ),
                    ContractBase.to_checksum_address(
                        datatoken_args.publish_market_order_fees.address
                    ),
                    ContractBase.to_checksum_address(
                        datatoken_args.publish_market_order_fees.token
                    ),
                ],
                [datatoken_args.cap, datatoken_args.publish_market_order_fees.amount],
                datatoken_args.bytess,
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
            {"from": wallet},
        )

        registered_nft_event = receipt.events["NFTCreated"]
        data_nft_address = registered_nft_event["newTokenAddress"]
        data_nft_token = DataNFT(self.config_dict, data_nft_address)

        registered_token_event = receipt.events["TokenCreated"]
        datatoken_address = registered_token_event["newTokenAddress"]
        datatoken = (
            Datatoken(self.config_dict, datatoken_address)
            if datatoken_args.template_index == 1
            else DatatokenEnterprise(self.config_dict, datatoken_address)
        )

        registered_fixed_rate_event = receipt.events["NewFixedRate"]
        exchange_id = registered_fixed_rate_event["exchangeId"]
        fixed_rate_exchange = FixedRateExchange(
            self.config_dict, get_address_of_type(self.config_dict, "FixedPrice")
        )
        exchange = OneExchange(fixed_rate_exchange, exchange_id)

        return data_nft_token, datatoken, exchange

    @enforce_types
    def create_with_erc20_and_dispenser(
        self,
        data_nft_args,
        datatoken_args,
        dispenser_max_tokens: int,
        dispenser_max_balance: int,
        dispenser_with_mint: bool,
        dispenser_allowed_swapper: str,
        wallet,
    ) -> str:
        dispenser_address = get_address_of_type(self.config_dict, "Dispenser")

        receipt = self.contract.createNftWithErc20WithDispenser(
            (
                data_nft_args.name,
                data_nft_args.symbol,
                data_nft_args.template_index,
                data_nft_args.uri,
                data_nft_args.transferable,
                ContractBase.to_checksum_address(data_nft_args.owner or wallet.address),
            ),
            (
                datatoken_args.template_index,
                [datatoken_args.name, datatoken_args.symbol],
                [
                    ContractBase.to_checksum_address(
                        datatoken_args.minter or wallet.address
                    ),
                    ContractBase.to_checksum_address(
                        datatoken_args.fee_manager or wallet.address
                    ),
                    ContractBase.to_checksum_address(
                        datatoken_args.publish_market_order_fees.address
                    ),
                    ContractBase.to_checksum_address(
                        datatoken_args.publish_market_order_fees.token
                    ),
                ],
                [datatoken_args.cap, datatoken_args.publish_market_order_fees.amount],
                datatoken_args.bytess,
            ),
            (
                ContractBase.to_checksum_address(dispenser_address),
                dispenser_max_tokens,
                dispenser_max_balance,
                dispenser_with_mint,
                ContractBase.to_checksum_address(dispenser_allowed_swapper),
            ),
            {"from": wallet},
        )

        registered_nft_event = receipt.events["NFTCreated"]
        data_nft_address = registered_nft_event["newTokenAddress"]
        data_nft_token = DataNFT(self.config_dict, data_nft_address)

        registered_token_event = receipt.events["TokenCreated"]
        datatoken_address = registered_token_event["newTokenAddress"]
        datatoken = (
            Datatoken(self.config_dict, datatoken_address)
            if datatoken_args.template_index == 1
            else DatatokenEnterprise(self.config_dict, datatoken_address)
        )

        registered_dispenser_event = receipt.events["DispenserCreated"]
        assert registered_dispenser_event["datatokenAddress"] == datatoken_address

        return data_nft_token, datatoken

    @enforce_types
    def create_with_metadata(
        self,
        data_nft_args,
        metadata_state: int,
        metadata_decryptor_url: str,
        metadata_decryptor_address: bytes,
        metadata_flags: bytes,
        metadata_data: Union[str, bytes],
        metadata_data_hash: Union[str, bytes],
        metadata_proofs: List[MetadataProof],
        wallet,
    ) -> str:
        receipt = self.contract.createNftWithMetaData(
            (
                data_nft_args.name,
                data_nft_args.symbol,
                data_nft_args.template_index,
                data_nft_args.uri,
                data_nft_args.transferable,
                ContractBase.to_checksum_address(data_nft_args.owner or wallet.address),
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
            {"from": wallet},
        )
        registered_nft_event = receipt.events["NFTCreated"]
        data_nft_address = registered_nft_event["newTokenAddress"]
        data_nft_token = DataNFT(self.config_dict, data_nft_address)

        return data_nft_token

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
