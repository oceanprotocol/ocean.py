#!/usr/bin/python3

import re
import os
import shutil
import subprocess
import sys

print('===Check Python version')
s = subprocess.check_output('python --version', shell=True) #eg 'Python 2.7.17'
version = float(re.findall(' \d\.[\d|\d\d]', str(s))[0]) #eg 2.7
if version < 3.6:
    print('===Need >= Python 3.6')
    sys.exit(0)

print('===Check virtualenv')
if 'myenv' not in str(os.environ.get('VIRTUAL_ENV')):
    print("""
Virtual environment not running. Have you done these? 
python -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt""")
    sys.exit(0)
    
print('===Clone/update .sol sources: begin')
if not os.path.exists('../ocean-contracts'):
    print('===  Clone ocean-contracts')
    os.system('cd ..; git clone https://github.com/oceanprotocol/ocean-contracts; cd -')
else:
    print('===  Update ocean-contracts')
    os.system('cd ../ocean-contracts; git pull; cd -')
    
if not os.path.exists('../openzeppelin-contracts'): #note that we use v0.2.5 
    print('===  Clone openzeppelin-contracts')
    os.system('cd ..; git clone --branch v2.5.0 https://github.com/OpenZeppelin/openzeppelin-contracts.git; cd -')
    #don't need to ever update them, since it's an old version
print('===Clone/update .sol sources: done')

print('===Populate ./contracts')
if os.path.exists('./contracts'):
    os.system('rm -rf contracts')
os.mkdir('contracts')
os.system('cp ../ocean-contracts/contracts/*.sol contracts/')
os.system('cp ../ocean-contracts/contracts/*/*.sol contracts/')
os.system('cp ../ocean-contracts/contracts/*/*/*.sol contracts/')

os.system('cp ../openzeppelin-contracts/contracts/ownership/Ownable.sol contracts/')
os.system('cp ../openzeppelin-contracts/contracts/token/ERC20/ERC20.sol contracts/')
os.system('cp ../openzeppelin-contracts/contracts/token/ERC20/../../GSN/Context.sol contracts/')
os.system('cp ../openzeppelin-contracts/contracts/token/ERC20/./IERC20.sol contracts/')
os.system('cp ../openzeppelin-contracts/contracts/token/ERC20/../../math/SafeMath.sol contracts/')
os.system('cp ../openzeppelin-contracts/contracts/token/ERC20/../../utils/Address.sol contracts/')

os.system('cp fudged_contracts/*.sol contracts/')

#delete unwanted contracts
os.system('rm contracts/FeeManager.sol')
os.system('rm contracts/FeeCalculator.sol')

print('===Flatten imports in .sol files')
def inplace_change(filename, old_s, new_s):
    with open(filename) as f:
        s = f.read()
        if old_s not in s:
            return
    with open(filename, 'w') as f:
        s = s.replace(old_s, new_s)
        f.write(s)

import glob
for f in glob.glob('contracts/*.sol'):
    inplace_change(f, 'openzeppelin-solidity/contracts/', './')
    inplace_change(f, '../../', './')
    inplace_change(f, '../', './')
    inplace_change(f, 'fee/', '')
    inplace_change(f, 'GSN/', '')
    inplace_change(f, 'math/', '')
    inplace_change(f, 'token/', '')
    inplace_change(f, 'utils/', '')
    inplace_change(f, 'ERC20/', '')
    inplace_change(f, 'interfaces/', '')
    inplace_change(f, 'ownership/', '')


print('===Compile')
os.system('brownie compile')

print('===Done!')
