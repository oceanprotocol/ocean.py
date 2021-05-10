#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_lib.ocean.ocean import Ocean

config = {
    "network": "polygon",
    "metadataCacheUri": "https://aquarius.polygon.oceanprotocol.com/",
    "providerUri": "https://provider.polygon.oceanprotocol.com/",
}

ocean = Ocean(config)

# Commented because datatoken has been created but token address cannot be found
# -------------------------------------------------------------------------------
# from ocean_lib.web3_internal.wallet import Wallet
# wallet = Wallet(ocean.web3, private_key=private_key)
# datatoken = ocean.create_data_token(
#     "Strident Cuttlefish Token",
#     "STRCUT-81",
#     from_wallet=wallet,
#     blob=ocean.config.metadata_cache_uri,
# )
# -------------------------------------------------------------------------------

dtfactory = ocean.get_dtfactory()
tx_id = "0xaa3771ad84cdc5372d880f3feb6dc41943ddf8aae03ee66a93c0dc0f7874d7a2"
address = dtfactory.get_token_address(tx_id)
assert address, "new datatoken has no address"
