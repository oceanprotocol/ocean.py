#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

# configuration file
CONF_FILE_PATH = "~/ocean.conf"

# Env var names

# Toggle runtime type-checking
import configparser  # noqa isort:skip
import os  # noqa isort:skip

config = configparser.ConfigParser()
config.read(os.path.expanduser(CONF_FILE_PATH))

TYPECHECK = config["util"].getboolean("typecheck")
assert TYPECHECK is not None


if not TYPECHECK:
    # do nothing, just return the original function
    def noop(f):
        return f
