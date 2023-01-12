#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_lib.web3_internal.contract_base import ContractBase

"""
approvedTokens
balance
buyDTBatch
consumeFee
getApprovedTokens
getDispensersContracts
getFixedRatesContracts
getMinVestingPeriod
getOPCCollector
getOPCConsumeFee
getOPCFee
getOPCFees
getOPCProviderFee
isApprovedToken
isDispenserContract
isFixedRateContract
opcCollector
providerFee
routerOwner
swapNonOceanFee
swapOceanFee
updateOPCCollector
updateOPCFee
"""
class FactoryRouter(ContractBase):
    CONTRACT_NAME = "FactoryRouter"
