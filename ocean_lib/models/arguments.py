#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
import warnings
from typing import Any, Dict, List, Optional

from ocean_lib.models.data_nft import DataNFT
from ocean_lib.models.data_nft_factory import DataNFTFactoryContract
from ocean_lib.models.datatoken import Datatoken
from ocean_lib.models.datatoken_enterprise import DatatokenEnterprise
from ocean_lib.ocean.util import get_address_of_type, get_ocean_token_address
from ocean_lib.structures.file_objects import FilesType
from ocean_lib.web3_internal.constants import MAX_UINT256, ZERO_ADDRESS
from ocean_lib.web3_internal.contract_base import ContractBase

logger = logging.getLogger("ocean")


class DataNFTArguments:
    def __init__(
        self,
        name: str,
        symbol: str,
        template_index: Optional[int] = 1,
        additional_datatoken_deployer: Optional[str] = None,
        additional_metadata_updater: Optional[str] = None,
        uri: Optional[str] = None,
        transferable: Optional[bool] = None,
        owner: Optional[str] = None,
    ):
        """
        :param name: str name of data NFT if creating a new one
        :param symbol: str symbol of data NFT  if creating a new one
        :param template_index: int template index of the data NFT, by default is 1.
        :param additional_datatoken_deployer: str address of an additional ERC20 deployer.
        :param additional_metadata_updater: str address of an additional metadata updater.
        :param uri: str URL of the data NFT.
        """
        self.name = name
        self.symbol = symbol or name
        self.template_index = template_index
        self.additional_datatoken_deployer = (
            additional_datatoken_deployer or ZERO_ADDRESS
        )
        self.additional_metadata_updater = additional_metadata_updater or ZERO_ADDRESS
        self.uri = uri or "https://oceanprotocol.com/nft/"
        self.transferable = transferable or True
        self.owner = owner

    def deploy_contract(self, config_dict, wallet) -> DataNFT:
        address = get_address_of_type(config_dict, DataNFTFactoryContract.CONTRACT_NAME)
        data_nft_factory = DataNFTFactoryContract(config_dict, address)

        receipt = data_nft_factory.deployERC721Contract(
            self.name,
            self.symbol,
            self.template_index,
            self.additional_metadata_updater,
            self.additional_datatoken_deployer,
            self.uri,
            self.transferable,
            self.owner or wallet.address,
            {"from": wallet},
        )

        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message=".*Event log does not contain enough topics for the given ABI.*",
            )
            registered_event = receipt.events["NFTCreated"]

        data_nft_address = registered_event["newTokenAddress"]
        return DataNFT(config_dict, data_nft_address)


class DatatokenArguments:
    def __init__(
        self,
        name: Optional[str] = "Datatoken 1",
        symbol: Optional[str] = "DT1",
        template_index: Optional[int] = 1,
        minter: Optional[str] = None,
        fee_manager: Optional[str] = None,
        publish_market_order_fee_address: Optional[str] = None,
        publish_market_order_fee_token: Optional[str] = None,
        publish_market_order_fee_amount: Optional[int] = 0,
        bytess: Optional[List[bytes]] = None,
        services: Optional[list] = None,
        files: Optional[List[FilesType]] = None,
        consumer_parameters: Optional[List[Dict[str, Any]]] = None,
        cap: Optional[int] = None,
    ):
        if template_index == 2 and not cap:
            raise Exception("Cap is needed for Datatoken Enterprise token deployment.")

        self.cap = cap if template_index == 2 else MAX_UINT256

        self.name = name
        self.symbol = symbol
        self.template_index = template_index
        self.minter = minter
        self.fee_manager = fee_manager
        self.publish_market_order_fee_address = (
            publish_market_order_fee_address or ZERO_ADDRESS
        )
        self.publish_market_order_fee_token = publish_market_order_fee_token
        self.publish_market_order_fee_amount = publish_market_order_fee_amount
        self.bytess = bytess or [b""]
        self.services = services
        self.files = files
        self.consumer_parameters = consumer_parameters

    def create_datatoken(self, data_nft, wallet, with_services=False):
        config_dict = data_nft.config_dict
        OCEAN_address = get_ocean_token_address(config_dict)
        initial_list = data_nft.getTokensList()

        data_nft.contract.createERC20(
            self.template_index,
            [self.name, self.symbol],
            [
                ContractBase.to_checksum_address(self.minter or wallet.address),
                ContractBase.to_checksum_address(self.fee_manager or wallet.address),
                ContractBase.to_checksum_address(self.publish_market_order_fee_address),
                ContractBase.to_checksum_address(
                    self.publish_market_order_fee_token or OCEAN_address
                ),
            ],
            [self.cap, self.publish_market_order_fee_amount],
            self.bytess,
            {"from": wallet},
        )

        new_elements = [
            item for item in data_nft.getTokensList() if item not in initial_list
        ]
        assert len(new_elements) == 1, "new data token has no address"

        datatoken = (
            Datatoken(config_dict, new_elements[0])
            if self.template_index == 1
            else DatatokenEnterprise(config_dict, new_elements[0])
        )

        logger.info(
            f"Successfully created datatoken with address " f"{datatoken.address}."
        )

        if with_services:
            if not self.services:
                self.services = [
                    datatoken.build_access_service(
                        service_id="0",
                        service_endpoint=config_dict.get("PROVIDER_URL"),
                        files=self.files,
                        consumer_parameters=self.consumer_parameters,
                    )
                ]
            else:
                for service in self.services:
                    service.datatoken = datatoken.address

        return datatoken
