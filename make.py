#! ./myenv/bin/python3

import re
import os
import shutil
import subprocess
import sys

from ocean_lib.constants import BROWNIEDIR

print('===Begin make.py')
CONTRACTDIR = f'./{BROWNIEDIR}/contracts'
print(f'  BROWNIEDIR: {BROWNIEDIR}')
print(f'  CONTRACTDIR: {CONTRACTDIR}')
assert '/' not in BROWNIEDIR

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

print(f'===Initialize {BROWNIEDIR}/')
if os.path.exists(f'./{BROWNIEDIR}'):
    os.system(f'rm -rf {BROWNIEDIR}')
os.system(f'brownie init {BROWNIEDIR}')

print(f'===Populate {CONTRACTDIR}')
os.system(f'cp ../ocean-contracts/contracts/*.sol {CONTRACTDIR}')
os.system(f'cp ../ocean-contracts/contracts/*/*.sol {CONTRACTDIR}')
os.system(f'cp ../ocean-contracts/contracts/*/*/*.sol {CONTRACTDIR}')

os.system(f'cp ../openzeppelin-contracts/contracts/ownership/Ownable.sol {CONTRACTDIR}/')
os.system(f'cp ../openzeppelin-contracts/contracts/token/ERC20/ERC20.sol {CONTRACTDIR}/')
os.system(f'cp ../openzeppelin-contracts/contracts/token/ERC20/../../GSN/Context.sol {CONTRACTDIR}/')
os.system(f'cp ../openzeppelin-contracts/contracts/token/ERC20/./IERC20.sol {CONTRACTDIR}')
os.system(f'cp ../openzeppelin-contracts/contracts/token/ERC20/../../math/SafeMath.sol {CONTRACTDIR}')
os.system(f'cp ../openzeppelin-contracts/contracts/token/ERC20/../../utils/Address.sol {CONTRACTDIR}')

os.system(f'cp fudged_contracts/*.sol {CONTRACTDIR}')

#delete unwanted contracts
os.system(f'rm {CONTRACTDIR}/FeeManager.sol')
os.system(f'rm {CONTRACTDIR}/FeeCalculator.sol')

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
for f in glob.glob(f'{CONTRACTDIR}/*.sol'):
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
os.system(f'cd {CONTRACTDIR}; brownie compile; cd -')

print('===Update abi/')
#these needed for ocean_lib/Ocean.py to be independent of brownie
os.system(f'cp {BROWNIEDIR}/build/contracts/DataTokenTemplate.json abi/')
os.system(f'cp {BROWNIEDIR}/build/contracts/Factory.json abi/')

print('===Done!')
