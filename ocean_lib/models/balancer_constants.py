#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

# ref: https://bankless.substack.com/p/how-to-create-your-own-balancer-pool
GASLIMIT_BFACTORY_NEWBPOOL = 5000000  # from ref above
GASLIMIT_BFACTORY_NEWMPOOL = 5000000  # from ref above

# from contracts/BConst.sol
# FIXME: grab info directly from contract
BCONST_BONE = 10 ** 18
BCONST_MIN_WEIGHT = BCONST_BONE  # Enforced in BPool.sol
BCONST_MAX_WEIGHT = BCONST_BONE * 50  # ""
BCONST_MAX_TOTAL_WEIGHT = BCONST_BONE * 50  # ""
BCONST_MIN_BALANCE = int(BCONST_BONE / 10 ** 12)  # "". value is 10**6

INIT_WEIGHT_DT = 9.0
INIT_WEIGHT_OCEAN = 1.0
INIT_WEIGHT_DT_BASE = BCONST_BONE * int(INIT_WEIGHT_DT)
INIT_WEIGHT_OCEAN_BASE = BCONST_BONE * int(INIT_WEIGHT_OCEAN)

DEFAULT_SWAP_FEE = 0.015  # 1.5%
DEFAULT_SWAP_FEE_BASE = int(BCONST_BONE * 0.015)  # 1.5%
