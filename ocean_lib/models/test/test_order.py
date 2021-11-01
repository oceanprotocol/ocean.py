#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os

from eth_utils import remove_0x_prefix
from ocean_lib.common.agreements.service_types import ServiceTypes
from ocean_lib.models.data_token import DataToken
from ocean_lib.models.order import Order
from ocean_lib.services.service import Service
from tests.resources.ddo_helpers import get_metadata, get_registered_ddo


def test_order(web3, alice_ocean, alice_wallet):
    asset = get_registered_ddo(alice_ocean, get_metadata(), alice_wallet)
    dt = DataToken(web3, asset.data_token_address)

    service = asset.get_service(service_type=ServiceTypes.ASSET_ACCESS)
    sa = Service.from_json(service.as_dictionary())

    order_requirements = alice_ocean.assets.order(
        asset.did, alice_wallet.address, sa.index
    )
    assert order_requirements, "Order was unsuccessful."

    _order_tx_id = alice_ocean.assets.pay_for_service(
        web3,
        order_requirements.amount,
        order_requirements.data_token_address,
        asset.did,
        service.index,
        alice_wallet.address,
        alice_wallet,
        sa.get_c2d_address(),
    )

    asset_folder = alice_ocean.assets.download(
        asset.did,
        sa.index,
        alice_wallet,
        _order_tx_id,
        alice_ocean.config.downloads_path,
    )

    assert len(os.listdir(asset_folder)) >= 1, "The asset folder is empty."
    for order_log in dt.get_start_order_logs():
        order_log_dict = dict(order_log.args.items())
        order_log_dict["amount"] = int(order_log.args.amount)
        order_log_dict["marketFee"] = int(order_log.args.marketFee)

        order_args = [
            order_log.address,
            order_log_dict["amount"],
            order_log_dict["timestamp"],
            order_log.transactionHash,
            f"did:op:{remove_0x_prefix(order_log.address)}",
            order_log_dict["payer"],
            order_log_dict["consumer"],
            order_log_dict["serviceId"],
            None,
        ]

        order = Order(*order_args)
        assert order, "The order does not exist."
        assert isinstance(order, tuple), "Order is not a tuple."
        assert (
            order[0] == asset.data_token_address
        ), "The order data token address is different."
        assert order[5] == alice_wallet.address, "The payer is not the supposed one."
        assert order[6] == sa.get_c2d_address(), "The consumer is not the supposed one."
        assert len(order) == 9, "Different number of args."
