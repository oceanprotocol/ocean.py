#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import Optional, Union

from enforce_typing import enforce_types
from web3.datastructures import AttributeDict
from ocean_lib.models.erc_token_factory_base import ERCTokenFactoryBase
from ocean_lib.models.fixed_rate_exchange import FixedRateExchange
from ocean_lib.structures.abi_tuples import (
    ChainMetadata,
    CreateErc20Data,
    CreateERC721Data,
    CreateERC721DataNoDeployer,
    DispenserData,
    FixedData,
    PoolData,
)
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
        self, erc721_data: Union[dict, tuple, CreateERC721Data], from_wallet: Wallet
    ):
        return self.send_transaction("deployERC721Contract", erc721_data, from_wallet)

    def get_current_nft_count(self) -> int:
        return self.contract.caller.getCurrentNFTCount()

    def get_nft_template(self, template_index: int) -> list:
        return self.contract.caller.getNFTTemplate(template_index)

    def get_current_nft_template_count(self) -> int:
        return self.contract.caller.getCurrentNFTTemplateCount()

    def is_contract(self, account_address: str) -> bool:
        return self.contract.caller.isContract(account_address)

    def create_token(
        self, token_data: Union[list, dict, CreateErc20Data], from_wallet: Wallet
    ) -> str:
        return self.send_transaction("createToken", token_data, from_wallet)

    def get_current_token_count(self) -> int:
        return self.contract.caller.getCurrentTokenCount()

    def get_token_template(self, index: int) -> list:
        return self.contract.caller.getTokenTemplate(index)

    def get_current_template_count(self) -> int:
        return self.contract.caller.getCurrentTemplateCount()

    def template_count(self) -> int:
        return self.contract.caller.templateCount()

    def start_multiple_token_order(self, orders: list, from_wallet: Wallet) -> str:
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
        nft_create_data: Union[dict, tuple, CreateERC721DataNoDeployer],
        erc_create_data: Union[dict, tuple, CreateErc20Data],
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "createNftWithErc20", (nft_create_data, erc_create_data), from_wallet
        )

    def create_nft_erc20_with_pool(
        self,
        nft_create_data: Union[dict, tuple, CreateERC721DataNoDeployer],
        erc_create_data: Union[dict, tuple, CreateErc20Data],
        pool_data: Union[dict, tuple, PoolData],
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "createNftWithErc20WithPool",
            (nft_create_data, erc_create_data, pool_data),
            from_wallet,
        )

    def create_nft_erc20_with_fixed_rate(
        self,
        nft_create_data: Union[dict, tuple, CreateERC721DataNoDeployer],
        erc_create_data: Union[dict, tuple, CreateErc20Data],
        fixed_data: Union[dict, tuple, FixedData],
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "createNftWithErc20WithFixedRate",
            (nft_create_data, erc_create_data, fixed_data),
            from_wallet,
        )

    def create_nft_erc20_with_dispenser(
        self,
        nft_create_data: Union[dict, tuple, CreateERC721DataNoDeployer],
        erc_create_data: Union[dict, tuple, CreateErc20Data],
        dispenser_data: Union[dict, tuple, DispenserData],
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "createNftWithErc20WithDispenser",
            (nft_create_data, erc_create_data, dispenser_data),
            from_wallet,
        )

    def create_nft_with_metadata(
        self,
        nft_create_data: Union[dict, tuple, CreateERC721DataNoDeployer],
        metadata: Union[dict, tuple, ChainMetadata],
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "createNftWithMetaData",
            (nft_create_data, metadata),
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
