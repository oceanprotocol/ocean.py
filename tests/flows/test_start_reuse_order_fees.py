#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from datetime import datetime, timedelta, timezone
from time import sleep
from typing import Tuple

import pytest

from ocean_lib.agreements.service_types import ServiceTypes
from ocean_lib.assets.ddo import DDO
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.example_config import get_config_dict
from ocean_lib.models.data_nft import DataNFT
from ocean_lib.models.datatoken_base import DatatokenBase, TokenFeeInfo
from ocean_lib.models.factory_router import FactoryRouter
from ocean_lib.ocean.ocean_assets import OceanAssets
from ocean_lib.ocean.util import get_address_of_type, to_wei
from ocean_lib.services.service import Service
from ocean_lib.structures.file_objects import FilesType
from ocean_lib.web3_internal.constants import MAX_UINT256
from tests.resources.ddo_helpers import get_default_metadata, get_first_service_by_type
from tests.resources.helper_functions import (
    deploy_erc721_erc20,
    get_file1,
    get_provider_fees,
    get_publisher_wallet,
    get_wallet,
    int_units,
    transfer_bt_if_balance_lte,
)

fee_parametrisation = [
    # Small fees
    (0, "Ocean", "5", "6", "7"),
    (1, "MockDAI", "5", "6", "7"),
    (2, "MockUSDC", "5", "6", "7"),
    # Zero fees
    (3, "Ocean", "0", "0", "0"),
    (4, "MockUSDC", "0", "0", "0"),
    # Min fees
    (
        5,
        "Ocean",
        "0.000000000000000001",  # 1 wei
        "0.000000000000000001",  # 1 wei
        "0.000000000000000001",  # 1 wei
    ),
    (6, "MockUSDC", "0.000001", "0.000001", "0.000001"),  # Smallest USDC amounts
    # Large fees
    (7, "Ocean", "500", "600", "700"),
    (8, "MockUSDC", "500", "600", "700"),
]


class TestStartReuseOrderFees(object):
    @classmethod
    def setup_class(self):
        self.ddos = []
        self.dts = []
        self.services = []
        self.start_order_receipts = []
        config = get_config_dict()
        publisher_wallet = get_publisher_wallet()
        file1 = get_file1()

        for index in range(9):
            data_nft = deploy_erc721_erc20(config, publisher_wallet)
            publish_market_wallet = get_wallet(4)
            bt = DatatokenBase.get_typed(
                config, get_address_of_type(config, fee_parametrisation[index][1])
            )

            publish_market_order_fee = int_units(
                fee_parametrisation[index][2], bt.decimals()
            )

            ddo, service, dt = create_asset_with_order_fee_and_timeout(
                config=config,
                file=file1,
                data_nft=data_nft,
                publisher_wallet=publisher_wallet,
                publish_market_order_fees=TokenFeeInfo(
                    address=publish_market_wallet.address,
                    token=bt.address,
                    amount=publish_market_order_fee,
                ),
                timeout=3600,
                wait_for_aqua=False,
            )

            self.ddos.append(ddo)
            self.dts.append(dt)
            self.services.append(service)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "param_index, base_token_name, publish_market_order_fee_in_unit, consume_market_order_fee_in_unit, provider_fee_in_unit",
        fee_parametrisation,
    )
    def test_start_order_fees(
        self,
        config: dict,
        publisher_wallet,
        consumer_wallet,
        provider_wallet,
        factory_deployer_wallet,
        factory_router: FactoryRouter,
        param_index: int,
        base_token_name: str,
        publish_market_order_fee_in_unit: str,
        consume_market_order_fee_in_unit: str,
        provider_fee_in_unit: str,
    ):
        bt = DatatokenBase.get_typed(
            config, get_address_of_type(config, base_token_name)
        )
        dt = self.dts[param_index]
        publish_market_wallet = get_wallet(4)
        consume_market_wallet = get_wallet(5)

        data_provider = DataServiceProvider
        ocean_assets = OceanAssets(config, data_provider)
        ddo = ocean_assets._aquarius.wait_for_ddo(self.ddos[param_index].did)

        publish_market_order_fee = int_units(
            publish_market_order_fee_in_unit, bt.decimals()
        )

        # Send base tokens to the consumer so they can pay for fees
        transfer_bt_if_balance_lte(
            config=config,
            bt_address=bt.address,
            from_wallet=factory_deployer_wallet,
            recipient=consumer_wallet.address,
            min_balance=int_units("2000", bt.decimals()),
            amount_to_transfer=int_units("2000", bt.decimals()),
        )

        # Mint 50 datatokens in consumer wallet from publisher.
        dt.mint(
            consumer_wallet.address,
            to_wei(50),
            {"from": publisher_wallet},
        )

        opc_collector_address = factory_router.getOPCCollector()

        if base_token_name == "Ocean" and publish_market_order_fee_in_unit == "500":
            bt.mint(
                consumer_wallet.address,
                int_units("2000", bt.decimals()),
                {"from": factory_deployer_wallet},
            )

        # Get balances
        publisher_bt_balance_before = bt.balanceOf(publisher_wallet.address)
        publisher_dt_balance_before = dt.balanceOf(publisher_wallet.address)
        publish_market_bt_balance_before = bt.balanceOf(publish_market_wallet.address)
        publish_market_dt_balance_before = dt.balanceOf(publish_market_wallet.address)
        consume_market_bt_balance_before = bt.balanceOf(consume_market_wallet.address)
        consume_market_dt_balance_before = dt.balanceOf(consume_market_wallet.address)
        consumer_bt_balance_before = bt.balanceOf(consumer_wallet.address)
        consumer_dt_balance_before = dt.balanceOf(consumer_wallet.address)
        provider_bt_balance_before = bt.balanceOf(provider_wallet.address)
        provider_dt_balance_before = dt.balanceOf(provider_wallet.address)
        opc_bt_balance_before = bt.balanceOf(opc_collector_address)
        opc_dt_balance_before = dt.balanceOf(opc_collector_address)

        # Get provider fees
        provider_fee = int_units(provider_fee_in_unit, bt.decimals())
        valid_for_two_hours = int(
            (datetime.now(timezone.utc) + timedelta(hours=2)).timestamp()
        )
        provider_fees = get_provider_fees(
            provider_wallet,
            bt.address,
            provider_fee,
            valid_for_two_hours,
        )

        # Grant datatoken infinite approval to spend consumer's base tokens
        bt.approve(dt.address, MAX_UINT256, {"from": consumer_wallet})

        # Start order for consumer
        consume_market_order_fee = int_units(
            consume_market_order_fee_in_unit, bt.decimals()
        )
        start_order_receipt = dt.start_order(
            consumer=consumer_wallet.address,
            service_index=ddo.get_index_of_service(self.services[param_index]),
            provider_fees=provider_fees,
            consume_market_fees=TokenFeeInfo(
                address=consume_market_wallet.address,
                token=bt.address,
                amount=consume_market_order_fee,
            ),
            tx_dict={"from": consumer_wallet},
        )

        self.start_order_receipts.append(start_order_receipt)

        # Get balances
        publisher_bt_balance_after = bt.balanceOf(publisher_wallet.address)
        publisher_dt_balance_after = dt.balanceOf(publisher_wallet.address)
        publish_market_bt_balance_after = bt.balanceOf(publish_market_wallet.address)
        publish_market_dt_balance_after = dt.balanceOf(publish_market_wallet.address)
        consume_market_bt_balance_after = bt.balanceOf(consume_market_wallet.address)
        consume_market_dt_balance_after = dt.balanceOf(consume_market_wallet.address)
        consumer_bt_balance_after = bt.balanceOf(consumer_wallet.address)
        consumer_dt_balance_after = dt.balanceOf(consumer_wallet.address)
        provider_bt_balance_after = bt.balanceOf(provider_wallet.address)
        provider_dt_balance_after = dt.balanceOf(provider_wallet.address)
        opc_bt_balance_after = bt.balanceOf(opc_collector_address)
        opc_dt_balance_after = dt.balanceOf(opc_collector_address)

        # Get order fee amount
        assert dt.get_publish_market_order_fees().amount == publish_market_order_fee

        # Get Ocean community fee amount
        opc_order_fee = factory_router.getOPCConsumeFee()
        assert opc_order_fee == to_wei(0.03)

        one_datatoken = to_wei(1)

        # Check balances
        assert publisher_bt_balance_before == publisher_bt_balance_after
        assert (
            publisher_dt_balance_before + one_datatoken - opc_order_fee
            == publisher_dt_balance_after
        )
        assert (
            publish_market_bt_balance_before + publish_market_order_fee
            == publish_market_bt_balance_after
        )
        assert publish_market_dt_balance_before == publish_market_dt_balance_after
        assert (
            consume_market_bt_balance_before + consume_market_order_fee
            == consume_market_bt_balance_after
        )
        assert consume_market_dt_balance_before == consume_market_dt_balance_after
        assert (
            consumer_bt_balance_before
            - publish_market_order_fee
            - consume_market_order_fee
            - provider_fee
            == consumer_bt_balance_after
        )
        assert consumer_dt_balance_before - one_datatoken == consumer_dt_balance_after
        assert provider_bt_balance_before + provider_fee == provider_bt_balance_after
        assert provider_dt_balance_before == provider_dt_balance_after
        assert opc_bt_balance_before == opc_bt_balance_after
        assert opc_dt_balance_before + opc_order_fee == opc_dt_balance_after

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "param_index",
        range(9),
    )
    def test_reuse_order_fees(
        self,
        config: dict,
        publisher_wallet,
        consumer_wallet,
        provider_wallet,
        param_index,
    ):
        publish_market_wallet = get_wallet(4)
        consume_market_wallet = get_wallet(5)

        base_token_name = fee_parametrisation[param_index][1]
        provider_fee_in_unit = fee_parametrisation[param_index][4]
        bt = DatatokenBase.get_typed(
            config, get_address_of_type(config, base_token_name)
        )
        dt = self.dts[param_index]
        start_order_receipt = self.start_order_receipts[param_index]

        # Reuse order where:
        #     Order: valid
        #     Provider fees: valid
        # Simulate valid provider fees by setting them to 0
        reuse_order_with_mock_provider_fees(
            provider_fee_in_unit="0",
            start_order_tx_id=start_order_receipt.transactionHash,
            bt=bt,
            dt=dt,
            publisher_wallet=publisher_wallet,
            publish_market_wallet=publish_market_wallet,
            consume_market_wallet=consume_market_wallet,
            consumer_wallet=consumer_wallet,
            provider_wallet=provider_wallet,
        )

        # Reuse order where:
        #     Order: valid
        #     Provider fees: expired
        # Simulate expired provider fees by setting them to non-zero
        reuse_order_with_mock_provider_fees(
            provider_fee_in_unit=provider_fee_in_unit,
            start_order_tx_id=start_order_receipt.transactionHash,
            bt=bt,
            dt=dt,
            publisher_wallet=publisher_wallet,
            publish_market_wallet=publish_market_wallet,
            consume_market_wallet=consume_market_wallet,
            consumer_wallet=consumer_wallet,
            provider_wallet=provider_wallet,
        )

        # Sleep for 6 seconds, long enough for order to expire
        sleep(6)

        # Reuse order where:
        #     Order: expired
        #     Provider fees: valid
        # Simulate valid provider fees by setting them to 0
        reuse_order_with_mock_provider_fees(
            provider_fee_in_unit="0",
            start_order_tx_id=start_order_receipt.transactionHash,
            bt=bt,
            dt=dt,
            publisher_wallet=publisher_wallet,
            publish_market_wallet=publish_market_wallet,
            consume_market_wallet=consume_market_wallet,
            consumer_wallet=consumer_wallet,
            provider_wallet=provider_wallet,
        )

        # Reuse order where:
        #     Order: expired
        #     Provider fees: expired
        # Simulate expired provider fees by setting them to non-zero
        reuse_order_with_mock_provider_fees(
            provider_fee_in_unit=provider_fee_in_unit,
            start_order_tx_id=start_order_receipt.transactionHash,
            bt=bt,
            dt=dt,
            publisher_wallet=publisher_wallet,
            publish_market_wallet=publish_market_wallet,
            consume_market_wallet=consume_market_wallet,
            consumer_wallet=consumer_wallet,
            provider_wallet=provider_wallet,
        )


def create_asset_with_order_fee_and_timeout(
    config: dict,
    file: FilesType,
    data_nft: DataNFT,
    publisher_wallet,
    publish_market_order_fees,
    timeout: int,
    wait_for_aqua: bool = True,
) -> Tuple[DDO, Service, DatatokenBase]:
    # Create datatoken with order fee
    datatoken = data_nft.create_datatoken(
        {"from": publisher_wallet},
        name="Datatoken 1",
        symbol="DT1",
        publish_market_order_fees=publish_market_order_fees,
    )

    data_provider = DataServiceProvider
    ocean_assets = OceanAssets(config, data_provider)
    metadata = get_default_metadata()
    files = [file]

    # Create service with timeout
    service = Service(
        service_id="5",
        service_type=ServiceTypes.ASSET_ACCESS,
        service_endpoint=data_provider.get_url(config),
        datatoken=datatoken.address,
        files=files,
        timeout=timeout,
    )

    # Publish asset
    data_nft, datatokens, ddo = ocean_assets.create(
        metadata=metadata,
        tx_dict={"from": publisher_wallet},
        services=[service],
        data_nft_address=data_nft.address,
        deployed_datatokens=[datatoken],
        wait_for_aqua=wait_for_aqua,
    )

    service = get_first_service_by_type(ddo, ServiceTypes.ASSET_ACCESS)

    return ddo, service, datatokens[0]


def reuse_order_with_mock_provider_fees(
    provider_fee_in_unit: str,
    start_order_tx_id: str,
    bt: DatatokenBase,
    dt: DatatokenBase,
    publisher_wallet,
    publish_market_wallet,
    consume_market_wallet,
    consumer_wallet,
    provider_wallet,
):
    """Call reuse_order, and verify the balances/fees are correct"""

    router = FactoryRouter(bt.config_dict, dt.router())
    opc_collector_address = router.getOPCCollector()

    # Get balances before reuse_order
    publisher_bt_balance_before = bt.balanceOf(publisher_wallet.address)
    publisher_dt_balance_before = dt.balanceOf(publisher_wallet.address)
    publish_market_bt_balance_before = bt.balanceOf(publish_market_wallet.address)
    publish_market_dt_balance_before = dt.balanceOf(publish_market_wallet.address)
    consume_market_bt_balance_before = bt.balanceOf(consume_market_wallet.address)
    consume_market_dt_balance_before = dt.balanceOf(consume_market_wallet.address)
    consumer_bt_balance_before = bt.balanceOf(consumer_wallet.address)
    consumer_dt_balance_before = dt.balanceOf(consumer_wallet.address)
    provider_bt_balance_before = bt.balanceOf(provider_wallet.address)
    provider_dt_balance_before = dt.balanceOf(provider_wallet.address)
    opc_bt_balance_before = bt.balanceOf(opc_collector_address)
    opc_dt_balance_before = dt.balanceOf(opc_collector_address)

    # Mock provider fees
    provider_fee = int_units(provider_fee_in_unit, bt.decimals())
    valid_until = int((datetime.now(timezone.utc) + timedelta(seconds=10)).timestamp())
    provider_fees = get_provider_fees(
        provider_wallet,
        bt.address,
        provider_fee,
        valid_until,
    )

    # Reuse order
    dt.reuse_order(
        order_tx_id=start_order_tx_id,
        provider_fees=provider_fees,
        tx_dict={"from": consumer_wallet},
    )

    # Get balances after reuse_order
    publisher_bt_balance_after = bt.balanceOf(publisher_wallet.address)
    publisher_dt_balance_after = dt.balanceOf(publisher_wallet.address)
    publish_market_bt_balance_after = bt.balanceOf(publish_market_wallet.address)
    publish_market_dt_balance_after = dt.balanceOf(publish_market_wallet.address)
    consume_market_bt_balance_after = bt.balanceOf(consume_market_wallet.address)
    consume_market_dt_balance_after = dt.balanceOf(consume_market_wallet.address)
    consumer_bt_balance_after = bt.balanceOf(consumer_wallet.address)
    consumer_dt_balance_after = dt.balanceOf(consumer_wallet.address)
    provider_bt_balance_after = bt.balanceOf(provider_wallet.address)
    provider_dt_balance_after = dt.balanceOf(provider_wallet.address)
    opc_bt_balance_after = bt.balanceOf(opc_collector_address)
    opc_dt_balance_after = dt.balanceOf(opc_collector_address)

    # Check balances
    assert publisher_bt_balance_before == publisher_bt_balance_after
    assert publisher_dt_balance_before == publisher_dt_balance_after
    assert publish_market_bt_balance_before == publish_market_bt_balance_after
    assert publish_market_dt_balance_before == publish_market_dt_balance_after
    assert consume_market_bt_balance_before == consume_market_bt_balance_after
    assert consume_market_dt_balance_before == consume_market_dt_balance_after
    assert consumer_bt_balance_before - provider_fee == consumer_bt_balance_after
    assert consumer_dt_balance_before == consumer_dt_balance_after
    assert provider_bt_balance_before + provider_fee == provider_bt_balance_after
    assert provider_dt_balance_before == provider_dt_balance_after
    assert opc_bt_balance_before == opc_bt_balance_after
    assert opc_dt_balance_before == opc_dt_balance_after
