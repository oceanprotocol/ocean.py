#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
from typing import Any, Optional

from enforce_typing import enforce_types

from ocean_lib.models.datatoken1 import Datatoken1


class Prediction:
    def __init__(self, prediction, stake):
        self.prediction = prediction
        self.stake = stake


class Datatoken3(Datatoken1):
    CONTRACT_NAME = "ERC20Template3"  # switch to ERC20Template3 when ready

    def __init__(self, config_dict: dict, address: str) -> None:
        super().__init__(config_dict, address)
        self.subscribers = {}  # [address] = timestamp
        self.predictions = {}  # [predict_blocknum][address] = Prediction

    # placeholders for now
    def submit_predval(self, token, prediction, stake, predict_blocknum, tx_dict):
        prediction = Prediction(prediction, stake)
        if predict_blocknum not in self.predictions:
            self.predictions[predict_blocknum] = {}
        self.predictions[predict_blocknum][tx_dict["from"]] = prediction
        token.transferFrom(
            tx_dict["from"], self.address, stake, {"from": self.address}
        )

    def get_agg_predval(self, stake, blocknum):
        pass

    def submit_trueval_and_payout(self, blocknum, prediction):
        pass

    def start_subscription(self, tx_dict):
        if tx_dict["from"] not in self.subscribers:
            self.subscribers[tx_dict["from"]] = 100  # mock timestamp
