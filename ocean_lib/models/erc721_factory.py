#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import List, Optional

from enforce_typing import enforce_types
from web3.datastructures import AttributeDict

from ocean_lib.models.erc_token_factory_base import ERCTokenFactoryBase
from ocean_lib.models.fixed_rate_exchange import FixedRateExchange
from ocean_lib.structures.abi_tuples import MetadataProof, OrderData
from ocean_lib.web3_internal.wallet import Wallet


@enforce_types
class ERC721FactoryContract(ERCTokenFactoryBase):
    CONTRACT_NAME = "ERC721Factory"
    EVENT_NFT_CREATED = "NFTCreated"
    EVENT_TOKEN_CREATED = "TokenCreated"
    EVENT_TEMPLATE721_ADDED = "Template721Added"
    EVENT_TEMPLATE20_ADDED = "Template20Added"
    EVENT_NEW_POOL = "NewPool"
    EVENT_NEW_FIXED_RATE = "NewFixedRate"
    EVENT_DISPENSER_CREATED = "DispenserCreated"

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

    def verify_nft(self, nft: str) -> bool:
        """Checks that a token was registered."""
        filter_args = {"newTokenAddress": nft}
        log = self.get_event_log(
            self.EVENT_NFT_CREATED, 0, self.web3.eth.block_number, filter_args
        )
        return bool(log and log[0].args.newTokenAddress == nft)

    def deploy_erc721_contract(
        self,
        name: str,
        symbol: str,
        template_index: int,
        additional_metadata_updater: str,
        additional_erc20_deployer: str,
        token_uri: str,
        from_wallet: Wallet,
    ):
        return self.send_transaction(
            "deployERC721Contract",
            (
                name,
                symbol,
                template_index,
                additional_metadata_updater,
                additional_erc20_deployer,
                token_uri,
            ),
            from_wallet,
        )

    def get_current_nft_count(self) -> int:
        return self.contract.caller.getCurrentNFTCount()

    def get_nft_template(self, template_index: int) -> list:
        return self.contract.caller.getNFTTemplate(template_index)

    def get_current_nft_template_count(self) -> int:
        return self.contract.caller.getCurrentNFTTemplateCount()

    def is_contract(self, account_address: str) -> bool:
        return self.contract.caller.isContract(account_address)

    def get_current_token_count(self) -> int:
        return self.contract.caller.getCurrentTokenCount()

    def get_token_template(self, index: int) -> list:
        return self.contract.caller.getTokenTemplate(index)

    def get_current_template_count(self) -> int:
        return self.contract.caller.getCurrentTemplateCount()

    def template_count(self) -> int:
        return self.contract.caller.templateCount()

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
        return self.send_transaction("startMultipleTokenOrder", (orders,), from_wallet)

    def create_nft_with_erc20(
        self,
        nft_name: str,
        nft_symbol: str,
        nft_template: int,
        token_uri: str,
        datatoken_template: int,
        datatoken_name: str,
        datatoken_symbol: str,
        datatoken_minter: str,
        datatoken_fee_manager: str,
        datatoken_publish_market_address: str,
        fee_token_address: str,
        datatoken_cap: int,
        publish_market_fee_amount: int,
        bytess: List[bytes],
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "createNftWithErc20",
            (
                (nft_name, nft_symbol, nft_template, token_uri),
                (
                    datatoken_template,
                    [datatoken_name, datatoken_symbol],
                    [
                        datatoken_minter,
                        datatoken_fee_manager,
                        datatoken_publish_market_address,
                        fee_token_address,
                    ],
                    [datatoken_cap, publish_market_fee_amount],
                    bytess,
                ),
            ),
            from_wallet,
        )

    def create_nft_erc20_with_pool(
        self,
        nft_name: str,
        nft_symbol: str,
        nft_template: int,
        token_uri: str,
        datatoken_template: int,
        datatoken_name: str,
        datatoken_symbol: str,
        datatoken_minter: str,
        datatoken_fee_manager: str,
        datatoken_publish_market_address: str,
        fee_token_address: str,
        datatoken_cap: int,
        publish_market_fee_amount: int,
        bytess: List[bytes],
        pool_ss_params: List[int],
        swap_fees: List[int],
        pool_addresses: List[str],
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "createNftWithErc20WithPool",
            (
                (nft_name, nft_symbol, nft_template, token_uri),
                (
                    datatoken_template,
                    [datatoken_name, datatoken_symbol],
                    [
                        datatoken_minter,
                        datatoken_fee_manager,
                        datatoken_publish_market_address,
                        fee_token_address,
                    ],
                    [datatoken_cap, publish_market_fee_amount],
                    bytess,
                ),
                (pool_ss_params, swap_fees, pool_addresses),
            ),
            from_wallet,
        )

    def create_nft_erc20_with_fixed_rate(
        self,
        nft_name: str,
        nft_symbol: str,
        nft_template: int,
        token_uri: str,
        datatoken_template: int,
        datatoken_name: str,
        datatoken_symbol: str,
        datatoken_minter: str,
        datatoken_fee_manager: str,
        datatoken_publish_market_address: str,
        fee_token_address: str,
        datatoken_cap: int,
        publish_market_fee_amount: int,
        bytess: List[bytes],
        fixed_price_address: str,
        fixed_rate_addresses: List[str],
        fixed_rate_uints: List[int],
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "createNftWithErc20WithFixedRate",
            (
                (nft_name, nft_symbol, nft_template, token_uri),
                (
                    datatoken_template,
                    [datatoken_name, datatoken_symbol],
                    [
                        datatoken_minter,
                        datatoken_fee_manager,
                        datatoken_publish_market_address,
                        fee_token_address,
                    ],
                    [datatoken_cap, publish_market_fee_amount],
                    bytess,
                ),
                (fixed_price_address, fixed_rate_addresses, fixed_rate_uints),
            ),
            from_wallet,
        )

    def create_nft_erc20_with_dispenser(
        self,
        nft_name: str,
        nft_symbol: str,
        nft_template: int,
        token_uri: str,
        datatoken_template: int,
        datatoken_name: str,
        datatoken_symbol: str,
        datatoken_minter: str,
        datatoken_fee_manager: str,
        datatoken_publish_market_address: str,
        fee_token_address: str,
        datatoken_cap: int,
        publish_market_fee_amount: int,
        bytess: List[bytes],
        dispenser_address: str,
        max_tokens: int,
        max_balance: int,
        with_mint: bool,
        allowed_swapper: str,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "createNftWithErc20WithDispenser",
            (
                (nft_name, nft_symbol, nft_template, token_uri),
                (
                    datatoken_template,
                    [datatoken_name, datatoken_symbol],
                    [
                        datatoken_minter,
                        datatoken_fee_manager,
                        datatoken_publish_market_address,
                        fee_token_address,
                    ],
                    [datatoken_cap, publish_market_fee_amount],
                    bytess,
                ),
                (
                    dispenser_address,
                    max_tokens,
                    max_balance,
                    with_mint,
                    allowed_swapper,
                ),
            ),
            from_wallet,
        )

    def create_nft_with_metadata(
        self,
        nft_name: str,
        nft_symbol: str,
        nft_template: int,
        token_uri: str,
        metadata_state: int,
        metadata_decryptor_url: str,
        metadata_decryptor_address: str,
        flags: bytes,
        data: bytes,
        data_hash: bytes,
        metadata_proofs: List[MetadataProof],
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "createNftWithMetaData",
            (
                (nft_name, nft_symbol, nft_template, token_uri),
                (
                    metadata_state,
                    metadata_decryptor_url,
                    metadata_decryptor_address,
                    flags,
                    data,
                    data_hash,
                    metadata_proofs,
                ),
            ),
            from_wallet,
        )

    def get_token_created_event(
        self, from_block: int, to_block: int, token_address: str
    ) -> [AttributeDict]:
        """Retrieves event log of token registration."""
        filter_params = {"newTokenAddress": token_address}
        logs = self.get_event_log(
            self.EVENT_TOKEN_CREATED,
            from_block=from_block,
            to_block=to_block,
            filters=filter_params,
        )

        return logs[0] if logs else None

    def search_exchange_by_datatoken(
        self,
        fixed_rate_exchange: FixedRateExchange,
        datatoken: str,
        exchange_owner: Optional[str] = None,
    ) -> list:
        token_created_log = self.get_token_created_event(
            from_block=0, to_block=self.web3.eth.block_number, token_address=datatoken
        )
        assert (
            token_created_log
        ), f"No token with '{datatoken}' address was created before."
        from_block = token_created_log.blockNumber
        filter_args = {"dataToken": datatoken}
        if exchange_owner:
            filter_args["exchangeOwner"] = exchange_owner
        logs = fixed_rate_exchange.get_event_logs(
            event_name="ExchangeCreated",
            from_block=from_block,
            to_block=self.web3.eth.block_number,
            filters=filter_args,
        )
        return [item.args.exchangeId for item in logs]

    def get_token_address(self, tx_id: str):
        tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_id)
        registered_event = self.get_event_log(
            event_name=ERC721FactoryContract.EVENT_NFT_CREATED,
            from_block=tx_receipt.blockNumber,
            to_block=self.web3.eth.block_number,
            filters=None,
        )

        return registered_event[0].args.newTokenAddress
