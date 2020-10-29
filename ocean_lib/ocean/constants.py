# configuration file
CONF_FILE_PATH = '~/ocean.conf'

# Toggle runtime type-checking
import configparser, os
config = configparser.ConfigParser()
config.read(os.path.expanduser(CONF_FILE_PATH))

TYPECHECK = config['util'].getboolean('typecheck')
assert TYPECHECK is not None


if not TYPECHECK:
    # do nothing, just return the original function
    def noop(f):
        return f

# Env var names
ENV_CONFIG_FILE = 'CONFIG_FILE'
ENV_PROVIDER_API_VERSION = 'PROVIDER_API_VERSION'
ENV_INFURA_CONNECTION_TYPE = 'INFURA_CONNECTION_TYPE'
ENV_INFURA_PROJECT_ID = 'INFURA_PROJECT_ID'
ENV_GAS_PRICE = 'GAS_PRICE'
ENV_MAX_GAS_PRICE = 'MAX_GAS_PRICE'

