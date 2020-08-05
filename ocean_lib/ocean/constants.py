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
