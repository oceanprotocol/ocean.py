
CONF_FILE_PATH = '~/ocean.conf'

DEFAULT_MINTING_CAP = 2**256 - 1

#V3 // Datatokens slides "Gas Cost Tests on Eth mainnet, Apr 27 2020" measured:
# -245000 gas to create new token.
# -70000 gas to mint 1 token (1st time)
# -40000 gas to mint 1 token (2nd, .. time)
# -79000 gas to transfer 10000 tokens
DEFAULT_GAS_LIMIT__CREATE_TOKEN = 245000 * 2 #2 for margin
DEFAULT_GAS_LIMIT__MINT_TOKENS = 70000 * 2 * 2 #2 for margin, 2 for our fees
DEFAULT_GAS_LIMIT__TRANSFER_TOKENS = 79000 * 2 #2 for margin
