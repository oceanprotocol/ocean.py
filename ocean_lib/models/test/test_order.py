#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os

from eth_utils import remove_0x_prefix

from ocean_lib.assets.asset import Asset
from ocean_lib.common.agreements.service_agreement import ServiceAgreement
from ocean_lib.common.agreements.service_types import ServiceTypes
from ocean_lib.models.data_token import DataToken
from ocean_lib.models.order import Order
from ocean_lib.ocean.util import from_base_18
from tests.resources.ddo_helpers import get_registered_ddo, get_metadata
from tests.resources.helper_functions import mint_tokens_and_wait


def test_order(alice_ocean, alice_wallet):
    asset = get_registered_ddo(alice_ocean, get_metadata(), alice_wallet)
    assert isinstance(asset, Asset)
    assert asset.data_token_address, "The asset does not have a token address."

    dt = DataToken(asset.data_token_address)
    mint_tokens_and_wait(dt, alice_wallet.address, alice_wallet)

    service = asset.get_service(service_type=ServiceTypes.ASSET_ACCESS)
    sa = ServiceAgreement.from_json(service.as_dictionary())

    order_requirements = alice_ocean.assets.order(
        asset.did, alice_wallet.address, sa.index
    )
    assert order_requirements, "Order was unsuccessful."

    args = [
        order_requirements.amount,
        order_requirements.data_token_address,
        asset.did,
        service.index,
        "0xF9f2DB837b3db03Be72252fAeD2f6E0b73E428b9",
        alice_wallet,
    ]
    _order_tx_id = alice_ocean.assets.pay_for_service(*args)

    asset_folder = alice_ocean.assets.download(
        asset.did,
        sa.index,
        alice_wallet,
        _order_tx_id,
        alice_ocean.config.downloads_path,
    )
    assert len(os.listdir(asset_folder)) >= 1, "The asset folder is empty."
    for order_log in dt.get_start_order_logs(alice_ocean.web3):
        order_log_dict = dict(order_log.args.items())
        order_log_dict["amount"] = from_base_18(int(order_log.args.amount))
        order_log_dict["marketFee"] = from_base_18(int(order_log.args.marketFee))

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
        assert order[1] == order_log_dict["amount"], "The ordered amount is different."
        assert order[2] == order_log_dict["timestamp"], "The timestamp is different."
        assert order[5] == order_log_dict["payer"]
        assert order[5] == alice_wallet.address, "The payer is not the supposed one."
        assert order[6] == order_log_dict["consumer"]
        assert order[6] == alice_wallet.address, "The consumer is not the supposed one."
        assert order[7] == order_log_dict["serviceId"]
        assert len(order) == 9, "Different number of args."
