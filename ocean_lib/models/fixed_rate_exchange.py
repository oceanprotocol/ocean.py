#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import Optional, Union

from enforce_typing import enforce_types

from ocean_lib.models.factory_router import FactoryRouter
from ocean_lib.ocean.util import get_address_of_type, get_from_address, str_with_wei
from ocean_lib.web3_internal.constants import MAX_UINT256, ZERO_ADDRESS
from ocean_lib.web3_internal.contract_base import ContractBase

checksum_addr = ContractBase.to_checksum_address


@enforce_types
class ExchangeArguments:
    def __init__(
        self,
        rate: Union[int, str],
        base_token_addr: str,
        owner_addr: Optional[str] = None,
        publish_market_fee_collector: Optional[str] = None,
        publish_market_fee: Union[int, str] = 0,
        with_mint: bool = True,
        allowed_swapper: str = ZERO_ADDRESS,
        full_info: bool = False,
        dt_decimals: Optional[int] = None,
    ):
        self.rate = rate
        self.base_token_addr = base_token_addr
        self.owner_addr = owner_addr
        self.publish_market_fee_collector = publish_market_fee_collector
        self.allowed_swapper = checksum_addr(allowed_swapper)
        self.rate = rate
        self.publish_market_fee = publish_market_fee
        self.with_mint = with_mint
        self.dt_decimals = dt_decimals

    def to_tuple(self, config_dict, tx_dict, dt_decimals=None):
        FRE_addr = get_address_of_type(config_dict, "FixedPrice")

        if not self.owner_addr:
            self.owner_addr = get_from_address(tx_dict)

        if not self.publish_market_fee_collector:
            self.publish_market_fee_collector = get_from_address(tx_dict)

        if not self.dt_decimals:
            if not dt_decimals:
                raise Exception(
                    "Must configure dt decimals either on arg creation or usage."
                )

            self.dt_decimals = dt_decimals

        # TODO: move to top now?
        from ocean_lib.models.datatoken_base import DatatokenBase  # isort:skip

        self.BT = DatatokenBase.get_typed(config_dict, self.base_token_addr)

        return (
            FRE_addr,
            [
                checksum_addr(self.BT.address),
                checksum_addr(self.owner_addr),
                self.publish_market_fee_collector,
                self.allowed_swapper,
            ],
            [
                self.BT.decimals(),
                self.dt_decimals,
                self.rate,
                self.publish_market_fee,
                self.with_mint,
            ],
        )


"""
Attributes:
MAX_FEE
MIN_FEE
MIN_RATE

Functions:

def balance() -> int:
    returns FRE balance
    :return: balance

def getExchanges() -> tuple:
    get list of exchange contracts addresses
    :return: tuple of contract addresses for each exchange

def generateExchangeId(bt_addr: str, dt_addr) -> str:
    retrieve exchange id based on a pair of basetoken-datatoken address pair
    :param bt_addr: address of base token
    :param dt_addr: address of datatoken
    :return: exchange id

def getId() -> int:
    get exchange id
    :return: id

def getNumberOfExchanges() -> int:
    get number of exchange contracts
    :return: number of exchanges


The following functions are wrapped with ocean.py helpers, especially in the OneExchange class, but you can use the raw form if needed.
buyDT
calcBaseInGivenOutDT
calcBaseOutGivenInDT
collectBT
collectDT
collectMarketFee
collectOceanFee
createWithDecimals -> raw creation of the exchange contract, much easier to use from datatoken.create_exchange()
getAllowedSwapper
getBTSupply
getDTSupply
getExchange
getFeesInfo
getMarketFee
getOPCFee
getRate
isActive
sellDT
setAllowedSwapper
setRate
toggleExchangeState
toggleMintState
updateMarketFee
updateMarketFeeCollector
"""


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
            f"  fixed_rate (price) = {str_with_wei(self.fixed_rate)}\n"
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
class ExchangeFeeInfo:
    def __init__(self, fees_tup):
        """
        :param:details_tup
          -- returned from FixedRateExchange.sol::getFeesInfo(exchange_id)
        which is {(publish)market(swap)Fee, ..., oceanFeeAvailable}
        """
        t = fees_tup
        self.publish_market_fee: int = t[0]
        self.publish_market_fee_collector: str = t[1]  # address
        self.opc_fee: int = t[2]
        self.publish_market_fee_available = t[3]  # in base tokens
        self.ocean_fee_available = t[4]  # in base tokens. Goes to OPC

    def __str__(self):
        s = (
            f"ExchangeFeeInfo: \n"
            f"  publish_market_fee = {str_with_wei(self.publish_market_fee)}\n"
            f"  publish_market_fee_available"
            f" = {str_with_wei(self.publish_market_fee_available)}\n"
            f"  publish_market_fee_collector"
            f" = {self.publish_market_fee_collector}\n"
            f"  opc_fee"
            f" = {str_with_wei(self.opc_fee)}\n"
            f"  ocean_fee_available (to opc)"
            f" = {str_with_wei(self.ocean_fee_available)}\n"
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

    def get_opc_collector(self) -> str:
        """Returns address that collects fees for Ocean Protocol Community"""
        router_addr = self.router()
        router = FactoryRouter(self.config_dict, router_addr)
        return router.getOPCCollector()


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
    def BT_needed(
        self,
        DT_amt: Union[int, str],
        consume_market_fee: Union[int, str],
        full_info: bool = False,
    ) -> Union[int, BtNeeded]:
        """
        Returns an int - how many BTs you need, to buy target amt of DTs.
        Or, for an object with all details, set full_info=True.
        """
        tup = self._FRE.calcBaseInGivenOutDT(self._id, DT_amt, consume_market_fee)
        bt_needed_obj = BtNeeded(tup)
        if full_info:
            return bt_needed_obj
        return bt_needed_obj.base_token_amount

    @enforce_types
    def BT_received(
        self,
        DT_amt: Union[int, str],
        consume_market_fee: Union[int, str],
        full_info: bool = False,
    ) -> Union[int, BtReceived]:
        """
        Returns an int - how many BTs you receive, in selling given amt of DTs.
        Or, for an object with all details, set full_info=True.
        """
        tup = self._FRE.calcBaseOutGivenInDT(self._id, DT_amt, consume_market_fee)
        bt_recd_obj = BtReceived(tup)
        if full_info:
            return bt_recd_obj
        return bt_recd_obj.base_token_amount

    @enforce_types
    def buy_DT(
        self,
        datatoken_amt: Union[int, str],
        tx_dict: dict,
        max_basetoken_amt=MAX_UINT256,
        consume_market_fee_addr: Optional[str] = ZERO_ADDRESS,
        consume_market_fee: Optional[Union[int, str]] = 0,
    ):
        """
        Buy datatokens via fixed-rate exchange.

        This wraps the smart contract method FixedRateExchange.buyDT()
          with a simpler interface.

        Params:
        - datatoken_amt - how many DT to buy? In wei, or str
        - max_basetoken_amt - maximum to spend
        - consume_market_fee_addr - market facilitating this swap
        - consume_market_fee - fee charged by market that's facilitating
        - tx_dict - e.g. {"from": alice_wallet}
        """
        # import now, to avoid circular import
        # TODO: maybe we can move it now?
        from ocean_lib.models.datatoken_base import DatatokenBase

        details = self.details
        BT = DatatokenBase.get_typed(self._FRE.config_dict, details.base_token)
        buyer_addr = get_from_address(tx_dict)

        BT_needed = self.BT_needed(datatoken_amt, consume_market_fee)
        assert BT.balanceOf(buyer_addr) >= BT_needed, "not enough funds"

        tx = self._FRE.buyDT(
            self._id,
            datatoken_amt,
            max_basetoken_amt,
            consume_market_fee_addr,
            consume_market_fee,
            tx_dict,
        )
        return tx

    @enforce_types
    def sell_DT(
        self,
        datatoken_amt: Union[int, str],
        tx_dict: dict,
        min_basetoken_amt: Union[int, str] = 0,
        consume_market_fee_addr: str = ZERO_ADDRESS,
        consume_market_fee: Union[int, str] = 0,
    ):
        """
        Sell datatokens to the exchange, in return for e.g. OCEAN

        This wraps the smart contract method FixedRateExchange.sellDT()
          with a simpler interface.

        Main params:
        - datatoken_amt - how many DT to sell? In wei, or str
        - min_basetoken_amt - min basetoken to get back
        - consume_market_fee_addr - market facilitating this swap
        - consume_market_fee - fee charged by market that's facilitating
        - tx_dict - e.g. {"from": alice_wallet}
        """
        tx = self._FRE.sellDT(
            self._id,
            datatoken_amt,
            min_basetoken_amt,
            consume_market_fee_addr,
            consume_market_fee,
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
    def collect_publish_market_fee(self, tx_dict: dict):
        """
        This exchange collects fees for the publishing market, and
          records updates into its `market_fee_available`.

        *This method* triggers the exchange to send all available market fees
          to this exchange's market fee collector (`market_fee_collector`).

        Anyone can call this method, since the receiver is constant.
        """
        return self._FRE.collectMarketFee(self._id, tx_dict)

    @enforce_types
    def collect_opc_fee(self, tx_dict: dict):
        """
        This exchange collects fees for the Ocean Protocol Community (OPC), and
          records updates into its `ocean_fee_available`.

        *This method* triggers the exchange to send all available OPC fees
          to the OPC Collector (router.getOPCCollector).

        Anyone can call this method, since the receiver is constant.
        """
        return self._FRE.collectOceanFee(self._id, tx_dict)

    @enforce_types
    def update_publish_market_fee_collector(self, new_addr: str, tx_dict):
        """Update which address collects the publish market swap fees"""
        return self._FRE.updateMarketFeeCollector(self._id, new_addr, tx_dict)

    @enforce_types
    def update_publish_market_fee(self, new_amt: Union[str, int], tx_dict):
        """Update the value of the publish market swap fee"""
        return self._FRE.updateMarketFee(self._id, new_amt, tx_dict)

    @enforce_types
    def get_publish_market_fee(self) -> int:
        """Return the value of the publish market swap fee"""
        return self._FRE.getMarketFee(self._id)

    @enforce_types
    def set_rate(self, new_rate: Union[int, str], tx_dict: dict):
        """Set price = # base tokens needed to buy 1 datatoken"""
        return self._FRE.setRate(self._id, new_rate, tx_dict)

    @enforce_types
    def toggle_mint_state(self, with_mint: bool, tx_dict: dict):
        """Switch 'with_mint' from True <> False"""
        return self._FRE.toggleMintState(self._id, with_mint, tx_dict)

    @enforce_types
    def toggle_active(self, tx_dict: dict):
        """Switch whether 'active' from True <> False"""
        return self._FRE.toggleExchangeState(self._id, tx_dict)

    @enforce_types
    def set_allowed_swapper(self, new_addr: str, tx_dict: dict):
        """Set allowed swapper. ZERO_ADDRESS means anyone can swap."""
        return self._FRE.setAllowedSwapper(self._id, new_addr, tx_dict)

    @enforce_types
    def get_rate(self) -> int:
        """Get price = # base tokens needed to buy 1 datatoken"""
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
        """Get allowed swapper. ZERO_ADDRESS means anyone can swap."""
        return self._FRE.getAllowedSwapper(self._id)

    @property
    def exchange_fees_info(self) -> ExchangeFeeInfo:
        """Get fee information for this exchange, as an object"""
        tup = self._FRE.getFeesInfo(self._id)
        return ExchangeFeeInfo(tup)

    @enforce_types
    def is_active(self) -> bool:
        """Get whether exchange is 'active'"""
        return self._FRE.isActive(self._id)
