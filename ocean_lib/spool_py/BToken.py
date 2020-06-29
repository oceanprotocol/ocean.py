import enforce

from ocean_lib.ocean import util

@enforce.runtime_validation
class BToken:
    def __init__(self, c: util.Context, address: str):
        self._c: util.Context = c
        abi = self._abi()
        self.contract = c.web3.eth.contract(address, abi=abi)
        
    @property
    def address(self):
        return self.contract.address
    
    def _abi(self):
        return util.abi(filename='./abi/BToken.abi')
    
    def balanceOfSelf_base(self) -> int:
        return self.balanceOf_base(self._c.address)

    def allowanceFromSelf_base(self, dst_address: str) -> int:
        src_address = self._c.address
        return self.allowance_base(src_address, dst_address)
        
    #============================================================
    #reflect BToken Solidity methods
    def symbol(self) -> str:
        return self.contract.functions.symbol().call()
    
    def decimals(self) -> int:
        return self.contract.functions.decimals().call()
    
    def balanceOf_base(self, address: str) -> int:
        func = self.contract.functions.balanceOf(address)
        return func.call()

    def approve(self, spender_address: str, amt_base: int):
        func = self.contract.functions.approve(spender_address, amt_base)
        util.buildAndSendTx(self._c, func)

    def transfer(self, dst_address: str, amt_base: int):
        func = self.contract.functions.transfer(dst_address, amt_base)
        util.buildAndSendTx(self._c, func)

    def allowance_base(self, src_address:str, dst_address: str) -> int:
        func = self.contract.functions.allowance(src_address, dst_address)
        return func.call()
