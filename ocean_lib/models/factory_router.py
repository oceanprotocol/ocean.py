#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_lib.web3_internal.contract_base import ContractBase

"""
# TODO should some of these functions be prohibited? constants hidden?
BONE
BPOW_PRECISION
EXIT_FEE
INIT_POOL_SUPPLY
MAX_BOUND_TOKENS
MAX_BPOW_BASE
MAX_FEE
MAX_IN_RATIO
MAX_OUT_RATIO
MAX_TOTAL_WEIGHT
MAX_WEIGHT
MIN_BALANCE
MIN_BOUND_TOKENS
MIN_BPOW_BASE
MIN_FEE
MIN_WEIGHT

addApprovedToken
addDispenserContract
addFactory
addFixedRateContract
addPoolTemplate
addSSContract
approvedTokens
balance
buyDTBatch
changeRouterOwner
consumeFee
deployDispenser
deployFixedRate
deployPool
dispensers
events
factory
fixedRate
fixedrates
getApprovedTokens
getDispensersContracts
getFixedRatesContracts
getMinVestingPeriod
getOPCCollector
getOPCConsumeFee
getOPCFee
getOPCFees
getOPCProviderFee
getPoolTemplates
getSSContracts
info ??
isApprovedToken
isDispenserContract
isFixedRateContract
isPoolTemplate
isSSContract
minVestingPeriodInBlocks
opcCollector
poolTemplates
providerFee
removeApprovedToken
removeDispenserContract
removeFixedRateContract
removePoolTemplate
removeSSContract
routerOwner
selectors
ssContracts
stakeBatch
swapNonOceanFee
swapOceanFee
topics
updateMinVestingPeriod
updateOPCCollector
updateOPCFee
"""
class FactoryRouter(ContractBase):
    CONTRACT_NAME = "FactoryRouter"
