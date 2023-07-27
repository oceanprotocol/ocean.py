#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_lib.example_config import get_config_dict
from ocean_lib.ocean.util import get_ocean_token_address


class DBSMock:
    def get_root_response(self):
        return [
            {
                "type": "filecoin",
                "description": "File storage on FileCoin",
                "payment": [
                    {
                        "chainId": 1,
                        "acceptedTokens": {
                            "OCEAN": "0xOCEAN_on_MAINNET",
                            "DAI": "0xDAI_ON_MAINNET",
                        },
                    },
                    {
                        "chainId": "polygon_chain_id",
                        "acceptedTokens": {
                            "OCEAN": "0xOCEAN_on_POLYGON",
                            "DAI": "0xDAI_ON_POLYGON",
                        },
                    },
                ],
            },
            {
                "type": "arweave",
                "description": "File storage on Arweave",
                "payment": [
                    {
                        "chainId": 1,
                        "acceptedTokens": {
                            "OCEAN": "0xOCEAN_on_MAINNET",
                            "DAI": "0xDAI_ON_MAINNET",
                        },
                    },
                    {
                        "chainId": "8996",
                        "acceptedTokens": {"ARWEAVE": "0xARWEAVEtoken_on_arweaveChain"},
                    },
                ],
            },
        ]

    def get_file_type_requirements(self, file_type, chain_id):
        response = self.get_root_response()
        for item in response:
            if item["type"] == file_type:
                for payment_item in item["payment"]:
                    if int(payment_item["chainId"]) == int(chain_id):
                        return payment_item["acceptedTokens"]

        return {}

    def get_quote(self, file_type, duration, chain_id, token_address, user_address):
        config = get_config_dict()
        from tests.resources.helper_functions import get_consumer_wallet

        consumer_wallet = get_consumer_wallet()

        return {
            "tokenAmount": 500,
            "approveAddress": consumer_wallet.address,
            "chainId": 1,
            "tokenAddress": get_ocean_token_address(config),
            "quoteId": "xxxx",
        }

    def upload_quote(self, quote_id, nonce, signature, f_file):
        return {}

    def get_status(self, quote_id) -> int:
        return 400

    def get_link(self, quote_id, nonce, signature):
        # TODO: could it be multiples?
        return [{"type": "arweave", "CID": "xxxx", "dealIDs": ["x", "x2"]}]
