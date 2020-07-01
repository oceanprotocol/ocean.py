
#ref: https://bankless.substack.com/p/how-to-create-your-own-balancer-pool
GASLIMIT_SFACTORY_NEWSPOOL = 5000000 # from ref above
GASLIMIT_SFACTORY_NEWMPOOL = 5000000 # from ref above

#from contracts/BConst.sol
# FIXME: grab info directly from contract
BCONST_BONE = 10**18
BCONST_MIN_WEIGHT = BCONST_BONE               #Enforced in SPool.sol
BCONST_MAX_WEIGHT = BCONST_BONE * 50          # ""
BCONST_MAX_TOTAL_WEIGHT = BCONST_BONE * 50    # ""
BCONST_MIN_BALANCE = int(BCONST_BONE/10**12)  # "". value is 10**6

INIT_WEIGHT_DT = BCONST_BONE * 1
INIT_WEIGHT_OCEAN = BCONST_BONE * 9

DEFAULT_SWAP_FEE = int(BCONST_BONE * 0.015) #1.5%
