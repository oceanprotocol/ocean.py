#!/usr/bin/python3

import os
import shutil
import sys

print("Check Python version")
version = sys.version_info
if not (version[0] >= 3 and version[1] >= 6):
    print("Need >= Python 3.6")
    sys.exit(0)

print("Check virtualenv")
if 'myenv' not in str(os.environ.get('VIRTUAL_ENV')):
    print("""
Virtual environment not running. Have you done these? 
python -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt""")
    sys.exit(0)
    
print('git clone .sol sources')
if not os.path.exists('../ocean-contracts'):
    os.system('cd ..; git clone https://github.com/oceanprotocol/ocean-contracts; cd -')
if not os.path.exists('../openzeppelin-contracts'):
    os.system('cd ..; git clone https://github.com/OpenZeppelin/openzeppelin-contracts.git; cd -')

print('populate ./contracts')
if os.path.exists('./contracts'):
    os.system('rm -rf contracts')
os.mkdir('contracts')
os.system('cp ../ocean-contracts/contracts/*.sol contracts/')
os.system('cp ../ocean-contracts/contracts/*/*.sol contracts/')
os.system('cp ../ocean-contracts/contracts/*/*/*.sol contracts/')

os.system('cp ../openzeppelin-contracts/contracts/token/ERC20/ERC20.sol contracts/')
os.system('cp ../openzeppelin-contracts/contracts/token/ERC20/../../GSN/Context.sol contracts/')
os.system('cp ../openzeppelin-contracts/contracts/token/ERC20/./IERC20.sol contracts/')
os.system('cp ../openzeppelin-contracts/contracts/token/ERC20/../../math/SafeMath.sol contracts/')
os.system('cp ../openzeppelin-contracts/contracts/token/ERC20/../../utils/Address.sol contracts/')

def inplace_change(filename, old_s, new_s):
    with open(filename) as f:
        s = f.read()
        if old_s not in s:
            return
    with open(filename, 'w') as f:
        s = s.replace(old_s, new_s)
        f.write(s)

print('flatten imports in .sol files')
import glob
for f in glob.glob("contracts/*.sol"):
    inplace_change(f, 'openzeppelin-solidity/contracts/', './')
    inplace_change(f, '../../', './')
    inplace_change(f, '../', './')
    inplace_change(f, 'fee/', '')
    inplace_change(f, 'GSN/', '')
    inplace_change(f, 'math/', '')
    inplace_change(f, 'token/', '')
    inplace_change(f, 'utils/', '')
    inplace_change(f, 'ERC20/', '')

print('brownie compile')
os.system('brownie compile')

print('final test')
#os.system('pytest')
