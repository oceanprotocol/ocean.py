#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import Optional, Union

from brownie import Wei
from enforce_typing import enforce_types

from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.ocean.util import str_with_wei



@enforce_types
class ExchangeDetails:
    def __init__(self, details_tup):
        """
        :param:details_tup
          -- returned from FixedRateExchange.sol::getExchange(exchange_id)
        which is (exchangeOwner, datatoken, .., withMint)
        """
        t = details_tup
        self.owner: str = t[0]
        self.datatoken: str = t[1]
        self.dt_decimals: int = t[2]
        self.base_token: str = t[3]
        self.bt_decimals: int = t[4]
        self.fixed_rate: int = t[5]
        self.active: bool = t[6]
        self.dt_supply: int = t[7]
        self.bt_supply: int = t[8]
        self.dt_balance: int = t[9]
        self.bt_balance: int = t[10]
        self.with_mint: bool = t[11]

    def __str__(self):
        s = (
            f"ExchangeDetails: \n"
            f"  datatoken = {self.datatoken}\n"
            f"  base_token = {self.base_token}\n"
            f"  price (fixed_rate) = {str_with_wei(self.fixed_rate)}\n"
            f"  active = {self.active}\n"
            f"  dt_supply = {str_with_wei(self.dt_supply)}\n"
            f"  bt_supply = {str_with_wei(self.bt_supply)}\n"
            f"  dt_balance = {str_with_wei(self.dt_balance)}\n"
            f"  bt_balance = {str_with_wei(self.bt_balance)}\n"
            f"  with_mint = {self.with_mint}\n"
            f"  dt_decimals = {self.dt_decimals}\n"
            f"  bt_decimals = {self.bt_decimals}\n"
            f"  owner = {self.owner}\n"
        )
        return s


@enforce_types
class Fees:
    def __init__(self, fees_tup):
        """
        :param:details_tup
          -- returned from FixedRateExchange.sol::getFeesInfo(exchange_id)
        which is (marketFee, marketFeeCollector, .., oceanFeeAvailable)
        """
        t = fees_tup
        self.market_fee: int = t[0]
        self.market_fee_collector: str = t[1]
        self.opc_fee: int = t[2]
        self.market_fee_available = t[3]
        self.ocean_fee_available = t[4]


    def __str__(self):
        s = (
            f"Fees: \n"
            f"  market_fee = {self.market_fee}\n"
            f"  market_fee_collector = {self.market_fee_collector}\n"
            f"  opc_fee = {self.opc_fee}\n"
            f"  market_fee_available = {self.market_fee_available}\n"
            f"  ocean_fee_available = {self.ocean_fee_available}\n"
        )
        return s


@enforce_types
class BtNeeded:
    def __init__(self, tup):
        self.base_token_amount = tup[0]
        self.ocean_fee_amount = tup[1]
        self.publish_market_fee_amount = tup[2]
        self.consume_market_fee_amount = tup[3]


@enforce_types
class BtReceived:
    def __init__(self, tup):
        self.base_token_amount = tup[0]
        self.ocean_fee_amount = tup[1]
        self.publish_market_fee_amount = tup[2]
        self.consume_market_fee_amount = tup[3]


@enforce_types
class FixedRateExchange(ContractBase):
    CONTRACT_NAME = "FixedRateExchange"


@enforce_types
class OneExchange:
    """
    Clean object-oriented class for a sole exchange, between two tokens.

    It's a bit like FixedRateExchange, but for just one exchange_id.
      Therefore its methods don't need the exchange_id argument.

    While it doesn't have a corresponding smart contract. It can be viewed as
      a slice of the FixedRateExchange contract.
    """

    @enforce_types
    def __init__(self, FRE: FixedRateExchange, exchange_id):
        self._FRE = FRE
        self._id = exchange_id


    @property
    def FRE(self):
        return self._FRE

    
    @property
    def exchange_id(self):
        return self._id


    @property
    def address(self):
        return self._FRE.address

    # From here on, the methods have a 1:1 mapping to FixedRateExchange.sol.
    # In some cases, there's a rename for better clarity
    # It's easy to tell the original method name: see what this class calls.


    @enforce_types
    def BT_needed(self, DT_amt: Union[int, str], full_info:bool=False) \
        -> Union[int, BtNeeded]:
        """
        Returns an int - how many BTs you need, to buy target amt of DTs.
        Or, for an object with all details, set full_info=True.
        """
        mkt_fee = self.fees.market_fee
        tup = self._FRE.calcBaseInGivenOutDT(self._id, DT_amt, mkt_fee)
        bt_needed_obj = BtNeeded(tup)
        if full_info:
            return bt_needed_obj
        return bt_needed_obj.base_token_amount


    @enforce_types
    def BT_received(self, DT_amt: Union[int, str], full_info:bool=False) \
        -> Union[int, BtReceived]:
        """
        Returns an int - how many BTs you receive, in selling given amt of DTs.
        Or, for an object with all details, set full_info=True.
        """
        mkt_fee = self.fees.market_fee
        tup = self._FRE.calcBaseOutGivenInDT(self._id, DT_amt, mkt_fee)
        bt_recd_obj = BtReceived(tup)
        if full_info:
            return bt_recd_obj
        return bt_recd_obj.base_token_amount


    @enforce_types
    def buy_DT(self,
               datatoken_amt: Union[int, str],
               tx_dict: dict,
               max_basetoken_amt: Optional[int] = None):
        """
        Buy datatokens via fixed-rate exchange.

        This wraps the smart contract method FixedRateExchange.buyDT()
          with a simpler interface.

        Main params:
        - datatoken_amt - how many DT to buy? In wei, or str
        - exchange_id -
        - tx_dict - e.g. {"from": alice_wallet}

        Optional params, with good defaults:
        - max_basetoken_amt - maximum to spend. Default is caller's balance.
        """
        # import now, to avoid circular import
        from ocean_lib.models.datatoken import Datatoken
        
        fees = self.fees
        details = self.details
        BT = Datatoken(self._FRE.config_dict, details.base_token)
        buyer_addr = tx_dict["from"].address

        if max_basetoken_amt is None:
            max_basetoken_amt = self.BT_needed(datatoken_amt)
        max_basetoken_amt = Wei(max_basetoken_amt)
        assert BT.balanceOf(buyer_addr) >= max_basetoken_amt, "not enough funds"
        
        tx = self._FRE.buyDT(
            self._id,
            datatoken_amt,
            max_basetoken_amt,
            fees.market_fee_collector,
            fees.market_fee,
            tx_dict,
        )
        return tx


    @enforce_types
    def sell_DT(self,
                datatoken_amt: Union[int, str],
                tx_dict: dict,
                min_basetoken_amt: Union[int, str] = 0):
        """
        Sell datatokens to the exchange, in return for e.g. OCEAN
        from the exchange's reserved

        This wraps the smart contract method FixedRateExchange.sellDT()
          with a simpler interface.

        Main params:
        - datatoken_amt - how many DT to sell? In wei, or str
        - exchange_id -
        - tx_dict - e.g. {"from": alice_wallet}

        Optional params, with good defaults:
        - min_basetoken_amt - min basetoken to get back
        """
        fees = self.fees

        tx = self._FRE.sellDT(
            self._id,
            datatoken_amt,
            min_basetoken_amt,
            fees.market_fee_collector,
            fees.market_fee,
            tx_dict,
        )
        return tx


    @enforce_types
    def collect_BT(self, amount: Union[int, str], tx_dict: dict):
        """
        This exchange collects fees denominated in base tokens, and 
          records updates into its `bt_balance`.

        *This method* triggers the exchange to send `amount` fees
          to the datatoken's payment collector (ERC20.getPaymentCollector)

        'amount' must be <= this exchange's bt_balance, of course.

        Anyone can call this method, since the receiver is constant.
        """
        return self._FRE.collectBT(self._id, amount, tx_dict)


    @enforce_types
    def collect_DT(self, amount: Union[int, str], tx_dict: dict):
        """
        This exchange collects fees denominated in datatokens, and 
          records updates into its `dt_balance`.

        *This method* triggers the exchange to send `amount` fees
          to the datatoken's payment collector (ERC20.getPaymentCollector)

        'amount' must be <= this exchange's dt_balance, of course.

        Anyone can call this method, since the receiver is constant.
        """
        return self._FRE.collectDT(self._id, amount, tx_dict)


    @enforce_types
    def collect_market_fee(self, tx_dict: dict):
        """
        This exchange collects fees for the publishing market, and
          records updates into its `market_fee_available`.

        *This method* triggers the exchange to send all available market fees
          to this exchange's market fee collector (`market_fee_collector`).

        Anyone can call this method, since the receiver is constant.
        """
        return self._FRE.collectMarketFee(self._id, tx_dict)


    @enforce_types
    def collect_ocean_fee(self, tx_dict: dict):
        """
        This exchange collects fees for the Ocean Protocol Community (OPC), and
          records updates into its `ocean_fee_available`.

        *This method* triggers the exchange to send all available OPC fees
          to the OPC Collector (router.getOPCCollector).

        Anyone can call this method, since the receiver is constant.
        """
        return self._FRE.collectOceanFee(self._id, tx_dict)


    @enforce_types
    def update_market_fee_collector(self, new_addr: str, tx_dict):
        return self._FRE.updateMarketFeeCollector(self._id, new_addr, tx_dict)


    @enforce_types
    def update_market_fee(self, new_amt: Union[str,int], tx_dict):
        return self._FRE.updateMarketFeeCollector(self._id, new_addr, tx_dict)


    @enforce_types
    def get_market_fee(self) -> int:
        return self._FRE.getMarketFee(self._id)


    @enforce_types
    def set_rate(self, new_rate: Union[int,str], tx_dict: dict):
        return self._FRE.setRate(self._id, new_rate, tx_dict)


    @enforce_types
    def toggle_mint_state(self, with_mint: bool, tx_dict: dict):
        return self._FRE.toggleMintState(self._id, with_mint, tx_dict)


    @enforce_types
    def toggle_active(self, tx_dict: dict):
        return self._FRE.toggleExchangeState(self._id, tx_dict)


    @enforce_types
    def set_allowed_swapper(self, new_addr: str, tx_dict: dict):
        return self._FRE.setAllowedSwapper(self._id, new_addr, tx_dict)


    @enforce_types
    def get_rate(self) -> int:
        """Return the current price (fixed rate) for this exchange"""
        return self._FRE.getRate(self._id)


    @enforce_types
    def get_dt_supply(self) -> int:
        """Return the current supply of datatokens in this exchange"""
        return self._FRE.getDTSupply(self._id)


    @enforce_types
    def get_bt_supply(self) -> int:
        """Return the current supply of base tokens in this exchange"""
        return self._FRE.getBTSupply(self._id)


    @property
    def details(self) -> ExchangeDetails:
        """Get all the exchange's details, as an object"""
        tup = self._FRE.getExchange(self._id)
        return ExchangeDetails(tup)


    @enforce_types
    def get_allowed_swapper(self) -> str:
        return self._FRE.getAllowedSwapper(self._id)


    @property
    def fees(self) -> Fees:
        tup = self._FRE.getFeesInfo(self._id) 
        return Fees(tup)


    @enforce_types
    def is_active(self) -> bool:
        return self._FRE.isActive(self._id)
