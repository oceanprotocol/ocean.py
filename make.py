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
shutil.copytree('../ocean-contracts/contracts', './contracts')
shutil.copyfile('../openzeppelin-contracts/contracts/token/ERC20/ERC20.sol', 'contracts/ERC20.sol')
shutil.copyfile('../openzeppelin-contracts/contracts/math/SafeMath.sol', 'contracts/SafeMath.sol')

print('clean up imports in .sol files')
os.system("cd contracts; find . -type f -exec sed -i 's/openzeppelin-solidity\/contracts\/math\//bar/g' {} +; cd -")
os.system("cd contracts; find . -type f -exec sed -i 's/openzeppelin-solidity\/contracts\/token\/ERC20\//bar/g' {} +; cd -")

print('brownie compile')
os.system('brownie compile')

print('final test')
os.system('pytest')
