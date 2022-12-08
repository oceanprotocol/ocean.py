#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import warnings
from typing import Optional

from ocean_lib.models.data_nft import DataNFT
from ocean_lib.models.data_nft_factory import DataNFTFactoryContract
from ocean_lib.ocean.util import get_address_of_type
from ocean_lib.web3_internal.constants import ZERO_ADDRESS


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
