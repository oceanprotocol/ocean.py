#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json
import warnings
from base64 import b64encode
from enum import IntEnum, IntFlag
from typing import Optional

from brownie import network
from enforce_typing import enforce_types
from web3 import Web3

from ocean_lib.models.datatoken_base import DatatokenArguments, DatatokenBase
from ocean_lib.ocean.util import (
    create_checksum,
    get_address_of_type,
    get_args_object,
    get_from_address,
)
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.utils import check_network

"""
def addManager(address: str) -> None:
    add a manager role to the address provided as a parameter
    :param address: address of interest
    :return: None

def addMultipleUsersToRoles(addresses: list, roles: list):
    add multiple users to multiple roles, mapping each address to the corresponding role in the list
    :param addresses: list of addresses
    :param roles: list of roles
    :return: None

def addTo725StoreList(address: str) -> None:
    add a role for storing datatokens to the address provided as a parameter
    :param address: address of interest
    :return: None

def addToCreateERC20List(address: str) -> None:
    add a role for deploying datatokens to the address provided as a parameter
    :param address: address of interest
    :return: None

def addToMetadataList(address: str) -> None:
    add a role for updating metadata to the address provided as a parameter
    :param address: address of interest
    :return: None

def approve(dst: str, tokenId: int) -> None:
    approve a token for address
    :param address: destination address
    :param tokenId: token Id
    :return: None

def balance() -> int:
    get token balance
    :return: int

def balanceOf(address: str) -> int:
    get token balance for specific address
    :param address: address of interest
    :return: int

def baseURI() -> str:
    get token baseURI
    :return: str

def cleanPermissions() -> None:
    reset all permissions on token,
    must include the tx_dict with the publisher as transaction sender
    :return: None

def executeCall(operation: int, dst: str, value: int, data: bytes) -> str:
    execute call
    :param operation: int representation of the operation to run
    :param dst: destination account address
    :param value: amount in wei
    :param data: operation data
    :return: transaction tx_id

def getApproved(tokenId: int) -> None:
    get approved address for a specific token Id
    :param tokenId: token Id
    :return: address

def getData(key: bytes32) -> bytes:
    get data assigned on token for specific key
    :param key: key of interest
    :return: value

def getId() -> int:
    get token Id
    :return: id

def getMetaData() -> tuple:
    get medatadata of token
    :return: tuple of decryptor url, decryptor address, metadata state, hasMetaData)

def getPermissions(user: str) -> tuple:
    get user permissions
    :param user: account address of interest
    :return: tuple of boolean values for manager role, deployer role, metadata updater role, store role

def getTokensList() -> list:
    get list of ERC20 tokens deployed on this NFT
    :return: list of token addresses

def hasMetaData() -> bool:
    :return: True if token has metadata, False otherwise

def isApprovedForAll(owner: str, operator: str) -> bool:
    returns if the operator is allowed to manage all the assets of owner.
    :param owner: address of owner
    :param operator: address of operator
    :return: bool

def metaDataDecryptorAddress() -> str:
    :return: address of metadata decryptor

def metaDataDecryptorUrl() -> str:
    :return: url of metadata decryptor

def metaDataState() -> int:
    :return: metadata state according to convention

def name() -> str:
    :return: name of token

def ownerOf(tokenId: int) -> str:
    get owner for a specific token Id
    :param tokenId: token Id
    :return: owner address

def removeFrom725StoreList(address: str) -> None:
    remove role for storing datatokens to the address provided as a parameter
    :param address: address of interest
    :return: None

def removeFromCreateERC20List(address: str) -> None:
    remove role for deploying datatokens to the address provided as a parameter
    :param address: address of interest
    :return: None

def removeFromMetadataList(address: str) -> None:
    remove role for updating metadata to the address provided as a parameter
    :param address: address of interest
    :return: None

def removeManager(address: str) -> None:
    remove manager role for the address provided as a parameter
    :param address: address of interest
    :return: None

def safeTransferFrom(from: str, to: str, token_id: int) -> TransactionReceipt:
    transfer ownership from one address to another
    :param from: address of current owner account
    :param to: address of destination account
    :param token_id: token Id
    :return: TransactionReceipt

def setApprovalForAll(operator: str, bool approved) -> None:
    approve or remove address as an operator for the token
    :param operator: address of operator
    :param approved: True for approval, False to revoke
    :return: None

def setBaseURI(base_uri: str) -> None:
    set token baseURI
    :param base_uri:
    :return: None

def setDataERC20(key: bytes, value: bytes) -> None:
    set a key, value pair on the token
    :param key:
    :param bytes:
    :return: None

def setMetaData(
    metaDataState: int,
    metaDataDecryptorUrl: str,
    metaDataDecryptorAddress: str,
    flags: bytes,
    data: bytes,
    metaDataHash: bytes,
    metadataProofs: list
) -> None:
    set token metadata, must include tx_dict with an authorized metadata updater as the sender
    :param metaDataState: metadata state as an int according to convention
    :param metaDataDecryptorUrl: metadata decryptor url
    :param metaDataDecryptorAddress: metadata decryptor address
    :param flags: encrypt/compress flags
    :param data: metadata (encoded as bytes)
    :param metaDataHash: metadata hash
    :param metadataProofs: list of tuples of valudator address and v, r, s signature values retrieved from validator
    :return: None

def setMetaDataAndTokenURI(
    metadataAndTokenURI: tuple,
) -> None:
    similar to setMetaData, set token metadata and token URI, must include tx_dict with an authorized metadata updater as the sender
    :param metadataAndTokenURI: tuple of the form (state, decryptor url, decryptor address, flags, data, hash, tokenURI, proofs)
    :return: None

def setMetaDataState(metaDataState: int) -> None:
    set token metadata state, must include tx_dict with an authorized metadata updater as the sender
    :param metaDataState: metadata state as an int according to convention
    :return: None

def setNewData(key: bytes, value: bytes) -> None:
    set a key, value pair on the token
    :param key:
    :param bytes:
    :return: None

def setTokenURI(tokenURI: str) -> None:
    set token URI, must include tx_dict with an authorized metadata updater as the sender
    :param tokenURI: token URI
    :return: None

def symbol() -> str:
    :return: symbol of token

def tokenByIndex(index: int) -> int:
    Returns a token ID at a given index of all the tokens stored by the contract
    :param index: int, index of a token
    :return: int id of the token

def tokenOfOwnerByIndex(owner: str, index: int) -> int:
    Returns a token ID owned by owner at a given index of all the tokens stored by the contract
    :param owner: owner address
    :param index: int, index of a token
    :return: int id of the token

def tokenURI() -> str:
    :return: tokenURI of token

def totalSupply() -> int:
    :return: total supply of token

def transferFrom(from: str, to: str, token_id: int) -> TransactionReceipt:
    transfer ownership from one address to another
    :param from: address of current owner account
    :param to: address of destination account
    :param token_id: token Id
    :return: TransactionReceipt

def transferable() -> bool:
    :return: True if token is transferable, False otherwise

def withdrawETH() -> None:
    withdraws all available ETH into the owner account
    :return: None


The following functions are wrapped with ocean.py helpers, but you can use the raw form if needed:
createERC20
"""


class DataNFTPermissions(IntEnum):
    MANAGER = 0
    DEPLOY_DATATOKEN = 1
    UPDATE_METADATA = 2
    STORE = 3


class MetadataState(IntEnum):
    ACTIVE = 0
    END_OF_LIFE = 1
    DEPRECATED = 2
    REVOKED = 3
    TEMPORARILY_DISABLED = 4


class Flags(IntFlag):
    PLAIN = 0
    COMPRESSED = 1
    ENCRYPTED = 2

    def to_byte(self):
        return self.to_bytes(1, "big")


@enforce_types
class DataNFT(ContractBase):
    CONTRACT_NAME = "ERC721Template"

    def create_datatoken(self, tx_dict, *args, **kwargs) -> DatatokenBase:
        datatoken_args = get_args_object(args, kwargs, DatatokenArguments)

        return datatoken_args.create_datatoken(self, tx_dict)

    def calculate_did(self):
        check_network(self.network)
        chain_id = network.chain.id
        return f"did:op:{create_checksum(self.address + str(chain_id))}"

    def set_data(self, field_label: str, field_value: str, tx_dict: dict):
        """Set key/value data via ERC725, with strings for key/value"""
        field_label_hash = Web3.keccak(text=field_label)  # to keccak256 hash
        field_value_bytes = field_value.encode()  # to array of bytes
        tx = self.contract.setNewData(field_label_hash, field_value_bytes, tx_dict)
        return tx

    def get_data(self, field_label: str) -> str:
        """Get key/value data via ERC725, with strings for key/value"""
        field_label_hash = Web3.keccak(text=field_label)  # to keccak256 hash
        field_value_hex = self.contract.getData(field_label_hash)
        field_value = field_value_hex.decode("ascii")
        return field_value


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
        self.uri = uri or self.get_default_token_uri()
        self.transferable = transferable or True
        self.owner = owner

    def get_default_token_uri(self):
        data = {
            "name": self.name,
            "symbol": self.symbol,
            "background_color": "141414",
            "image_data": "data:image/svg+xml,%3Csvg viewBox='0 0 99 99' fill='undefined' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath fill='%23ff409277' d='M0,99L0,29C9,24 19,19 31,19C42,18 55,23 67,25C78,26 88,23 99,21L99,99Z'/%3E%3Cpath fill='%23ff4092bb' d='M0,99L0,43C9,45 18,47 30,48C41,48 54,46 66,45C77,43 88,43 99,43L99,99Z'%3E%3C/path%3E%3Cpath fill='%23ff4092ff' d='M0,99L0,78C10,75 20,72 31,71C41,69 53,69 65,70C76,70 87,72 99,74L99,99Z'%3E%3C/path%3E%3C/svg%3E",
        }

        return b"data:application/json;base64," + b64encode(
            json.dumps(data, separators=(",", ":")).encode("utf-8")
        )

    def deploy_contract(self, config_dict, tx_dict) -> DataNFT:
        from ocean_lib.models.data_nft_factory import (  # isort:skip
            DataNFTFactoryContract,
        )

        address = get_address_of_type(config_dict, DataNFTFactoryContract.CONTRACT_NAME)
        data_nft_factory = DataNFTFactoryContract(config_dict, address)

        wallet_address = get_from_address(tx_dict)

        receipt = data_nft_factory.deployERC721Contract(
            self.name,
            self.symbol,
            self.template_index,
            self.additional_metadata_updater,
            self.additional_datatoken_deployer,
            self.uri,
            self.transferable,
            self.owner or wallet_address,
            tx_dict,
        )

        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message=".*Event log does not contain enough topics for the given ABI.*",
            )
            assert receipt and receipt.events, "Missing NFTCreated event"
            registered_event = receipt.events["NFTCreated"]

        data_nft_address = registered_event["newTokenAddress"]
        return DataNFT(config_dict, data_nft_address)
