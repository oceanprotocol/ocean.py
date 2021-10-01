#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import List

from enforce_typing import enforce_types
from ocean_lib.models.v4.erc_token_factory_base import ERCTokenFactoryBase
from ocean_lib.models.v4.factory_tuples import (
    NftCreateData,
    ErcCreateData,
    PoolData,
    FixedData,
)
from ocean_lib.web3_internal.wallet import Wallet


@enforce_types
class ERC721FactoryContract(ERCTokenFactoryBase):
    CONTRACT_NAME = "ERC721Factory"
    EVENT_NFT_CREATED = "NFTCreated"
    EVENT_TOKEN_CREATED = "TokenCreated"
    EVENT_NEW_POOL = "NewPool"
    EVENT_NEW_FIXED_RATE = "NewFixedRate"

    @property
    @enforce_types
    def event_TokenCreated(self):
        return self.events.NFTCreated()

    @property
    @enforce_types
    def event_TokenCreated(self):
        return self.events.TokenCreated()

    @property
    @enforce_types
    def event_NewPool(self):
        return self.events.NewPool()

    @property
    @enforce_types
    def event_NewFixedRate(self):
        return self.events.NewFixedRate()

    @enforce_types
    def deploy_erc721_contract(
        self,
        name: str,
        symbol: int,
        data: bytes,
        flags: bytes,
        template_index: int,
        from_wallet: Wallet,
    ):
        return self.send_transaction(
            "deployERC721Contract",
            (name, symbol, data, flags, template_index),
            from_wallet,
        )

    @enforce_types
    def get_current_token_count(self) -> int:
        return self.contract.caller.getCurrentNFTCount()

    @enforce_types
    def get_nft_template(self, template_index: int) -> list:
        return self.contract.caller.getNFTTemplate(template_index)

    @enforce_types
    def get_current_nft_template_count(self) -> int:
        return self.contract.caller.getCurrentNFTTemplateCount()

    @enforce_types
    def is_contract(self, account_address: str) -> bool:
        return self.contract.caller.isContract(account_address)

    @enforce_types
    def create_token(
        self,
        template_index: int,
        strings: List[str],
        addresses: List[str],
        uints: List[int],
        bytess: bytes,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "createToken",
            (template_index, strings, addresses, uints, bytess),
            from_wallet,
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
    def start_multiple_token_order(
        self,
        token_address: str,
        consumer: str,
        amount: int,
        service_id: int,
        consume_fee_address: str,
        consume_fee_token: str,
        consume_fee_amount: int,
        from_wallet: Wallet,
    ) -> str:
        orders = [
            [
                token_address,
                consumer,
                amount,
                service_id,
                consume_fee_address,
                consume_fee_token,
                consume_fee_amount,
            ]
        ]
        return self.send_transaction("startMultipleTokenOrder", orders, from_wallet)

    @enforce_types
    def create_nft_with_erc(
        self,
        nft_create_data: NftCreateData,
        erc_create_data: ErcCreateData,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "createNftWithErc",
            (
                [
                    nft_create_data.name,
                    nft_create_data.symbol,
                    nft_create_data.template_index,
                ],
                [
                    erc_create_data.template_index,
                    erc_create_data.strings,
                    erc_create_data.addresses,
                    erc_create_data.uints,
                    erc_create_data.bytess,
                ],
            ),
            from_wallet,
        )

    @enforce_types
    def create_nft_erc_with_pool(
        self,
        nft_create_data: NftCreateData,
        erc_create_data: ErcCreateData,
        pool_data: PoolData,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "createNftErcWithPool",
            (
                [
                    nft_create_data.name,
                    nft_create_data.symbol,
                    nft_create_data.template_index,
                ],
                [
                    erc_create_data.template_index,
                    erc_create_data.strings,
                    erc_create_data.addresses,
                    erc_create_data.uints,
                    erc_create_data.bytess,
                ],
                [
                    pool_data.controller,
                    pool_data.base_token,
                    pool_data.ss_params,
                    pool_data.bt_sender,
                    pool_data.swap_fees,
                    pool_data.market_fee_collector,
                    pool_data.publisher,
                ],
            ),
            from_wallet,
        )

    @enforce_types
    def createNftErcWithFixedRate(
        self,
        nft_create_data: NftCreateData,
        erc_create_data: ErcCreateData,
        fixed_data: FixedData,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "createNftErcWithPool",
            (
                [
                    nft_create_data.name,
                    nft_create_data.symbol,
                    nft_create_data.template_index,
                ],
                [
                    erc_create_data.template_index,
                    erc_create_data.strings,
                    erc_create_data.addresses,
                    erc_create_data.uints,
                    erc_create_data.bytess,
                ],
                [
                    fixed_data.fixed_price_address,
                    fixed_data.base_token,
                    fixed_data.bt_decimals,
                    fixed_data.exchange_rate,
                    fixed_data.owner,
                    fixed_data.market_fee,
                    fixed_data.market_fee_collector,
                ],
            ),
            from_wallet,
        )
