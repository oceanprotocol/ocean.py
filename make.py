#!/usr/bin/python3

import os

os.system('cp -r ../ocean-contracts/contracts .')

os.system('brownie compile')
