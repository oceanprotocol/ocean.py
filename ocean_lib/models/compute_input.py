#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import Any, Dict, Optional, Union

from enforce_typing import enforce_types

from ocean_lib.assets.asset import Asset
from ocean_lib.services.service import Service
from ocean_lib.structures.algorithm_metadata import AlgorithmMetadata
from ocean_lib.web3_internal.constants import ZERO_ADDRESS


class ComputeInput:
    @enforce_types
    def __init__(
        self,
        asset: Asset,
        service: Service,
        transfer_tx_id: Union[str, bytes] = None,
        userdata: Optional[Dict] = None,
        consume_market_order_fee_token: Optional[str] = None,
        consume_market_order_fee_amount: Optional[int] = None,
    ) -> None:
        """Initialise and validate arguments."""
        assert asset and service is not None, "bad argument values."

        if userdata:
            assert isinstance(userdata, dict), "Userdata must be a dictionary."

        self.asset = asset
        self.did = asset.did
        self.transfer_tx_id = transfer_tx_id
        self.service = service
        self.service_id = service.id
        self.userdata = userdata
        self.consume_market_order_fee_token = (
            consume_market_order_fee_token
            if consume_market_order_fee_token
            else ZERO_ADDRESS
        )
        self.consume_market_order_fee_amount = (
            consume_market_order_fee_amount if consume_market_order_fee_amount else 0
        )

    @enforce_types
    def as_dictionary(self) -> Dict[str, Union[str, Dict]]:
        res = {
            "documentId": self.did,
            "serviceId": self.service_id,
        }

        if self.userdata:
            res["userdata"] = self.userdata

        if self.transfer_tx_id:
            res["transferTxId"] = self.transfer_tx_id

        return res


class RawAlgoComputeInput:
    @enforce_types
    def __init__(
        self,
        algo_metadata: AlgorithmMetadata,
        consume_market_order_fee_token: Optional[str] = None,
        consume_market_order_fee_amount: Optional[int] = None,
    ) -> None:
        """Initialise and validate arguments."""
        self.algo_metadata = algo_metadata
        self.consume_market_order_fee_token = (
            consume_market_order_fee_token
            if consume_market_order_fee_token
            else ZERO_ADDRESS
        )
        self.consume_market_order_fee_amount = (
            consume_market_order_fee_amount if consume_market_order_fee_amount else 0
        )

    @enforce_types
    def as_dictionary(self) -> Dict[str, Any]:
        return self.algo_metadata.as_dictionary()
