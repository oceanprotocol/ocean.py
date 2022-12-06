#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enum import IntEnum

from enforce_typing import enforce_types
from web3 import Web3

from ocean_lib.web3_internal.contract_base import ContractBase


@enforce_types
class FreStatus:
    def __init__(self, status_tup):
        """
        :param:status_tup
          -- returned from FixedRateExchange.sol::getExchange(exchange_id)
        which is (exchangeOwner, datatoken, .., withMint)
        """
        t = status_tup
        self.exchangeOwner: str = t[0]
        self.datatoken: str = t[1]
        self.dtDecimals: int = t[2]
        self.baseToken: str = t[3]
        self.btDecimals: int = t[4]
        self.fixedRate: int = t[5]
        self.active: bool = t[6]
        self.dtSupply: int = t[7]
        self.btSupply: int = t[8]
        self.dtBalance: int = t[9]
        self.btBalance: int = t[10]
        self.withMint: bool = t[11]

    def __str__(self):
        s = (
            f"FreStatus: \n"
            f"  datatoken = {self.datatoken}\n"
            f"  baseToken = {self.baseToken}\n"
            f"  price in baseToken (fixedRate) = {_strWithWei(self.fixedRate)}\n"
            f"  active = {self.active}\n"
            f"  dtSupply = {_strWithWei(self.dtSupply)}\n"
            f"  btSupply = {_strWithWei(self.btSupply)}\n"
            f"  dtBalance = {_strWithWei(self.dtBalance)}\n"
            f"  btBalance = {_strWithWei(self.btBalance)}\n"
            f"  withMint = {self.withMint}\n"
            f"  dtDecimals = {self.dtDecimals}\n"
            f"  btDecimals = {self.btDecimals}\n"
            f"  exchangeOwner = {self.exchangeOwner}\n"
        )
        return s


@enforce_types
class FreFees:
    def __init__(self, fees_tup):
        """
        :param:status_tup
          -- returned from FixedRateExchange.sol::getFeesInfo(exchange_id)
        which is (marketFee, marketFeeCollector, .., oceanFeeAvailable)
        """
        t = fees_tup
        self.marketFee: int = t[0]
        self.marketFeeCollector: str = t[1]
        self.opcFee: int = t[2]
        self.marketFeeAvailable = t[3]
        self.oceanFeeAvailable = t[4]


    def __str__(self):
        s = (
            f"FreFees: \n"
            f"  marketFee = {self.marketFee}\n"
            f"  marketFeeCollector = {self.marketFeeCollector}\n"
            f"  opcFee = {self.opcFee}\n"
            f"  marketFeeAvailable = {self.marketFeeAvailable}\n"
            f"  oceanFeeAvailable = {self.oceanFeeAvailable}\n"
        )
        return s


@enforce_types
class BtNeeded:
    def __init__(self, tup):
        self.val = tup[0] #baseTokenAmount
        self.oceanFeeAmount = tup[1]
        self.publishMarketFeeAmount = tup[2]
        self.consumeMarketFeeAmount = tup[3]


@enforce_types
class BtReceived:
    def __init__(self, tup):
        self.val = tup[0] #baseTokenAmount
        self.oceanFeeAmount = tup[1]
        self.publishMarketFeeAmount = tup[2]
        self.consumeMarketFeeAmount = tup[3]


@enforce_types
class FixedRateExchange(ContractBase):
    CONTRACT_NAME = "FixedRateExchange"

    def fees(self, exchange_id) -> FreFees:
        fees_tup = self.contract.getFeesInfo(exchange_id) 
        return FreFees(fees_tup)


    def status(self, exchange_id) -> FreStatus:
        status_tup = self.contract.getExchange(exchange_id)
        return FreStatus(status_tup)


    def BT_needed(self, exchange_id, DT_amt) -> BtNeeded:
        """How many BTs you need, to buy target amt of DTs (buyDT)"""
        mkt_fee = self.fees(exchange_id).marketFee
        tup = self.contract.calcBaseInGivenOutDT(exchange_id, DT_amt, mkt_fee)
        return BtNeeded(tup)


    def BT_received(self, exchange_id, DT_amt) -> BtReceived:
        """How many BTs you receive, in selling given amt of DTs (sellDT)"""
        mkt_fee = self.fees(exchange_id).marketFee
        tup = self.contract.calcBaseOutGivenInDT(exchange_id, DT_amt, mkt_fee)
        return BtReceived(tup)


@enforce_types
def _strWithWei(x_wei: int) -> str:
    return f"{Web3.fromWei(x_wei, 'ether')} ({x_wei} wei)"
