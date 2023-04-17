pragma solidity 0.8.12;
// Copyright BigchainDB GmbH and Ocean Protocol contributors
// SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
// Code is Apache-2.0 and docs are CC-BY-4.0

contract ERC20Roles {
    
    
    mapping(address => RolesERC20) public permissions;

    address[] public authERC20;

    struct RolesERC20 {
        bool minter;
        bool paymentManager; 
    }

    event AddedMinter(
        address indexed user,
        address indexed signer,
        uint256 timestamp,
        uint256 blockNumber
    );
    event RemovedMinter(
        address indexed user,
        address indexed signer,
        uint256 timestamp,
        uint256 blockNumber
    );

    /**
    * @dev getPermissions
    *      Returns list of roles for an user
    * @param user user address
    */
    function getPermissions(address user) public view returns (RolesERC20 memory) {
        return permissions[user];
    }

    /**
     * @dev isMinter
     *      Check if an address has the minter role
     * @param account refers to an address that is checked
     */
    function isMinter(address account) public view returns (bool) {
        return (permissions[account].minter);
    }

    
    /**
    * @dev _addMinter
    *      Internal function to add minter role to an user.
    * @param _minter user address
    */
    function _addMinter(address _minter) internal {
        if(_minter != address(0)){
            RolesERC20 storage user = permissions[_minter];
            require(user.minter == false, "ERC20Roles:  ALREADY A MINTER");
            user.minter = true;
            _pushToAuthERC20(_minter);
            emit AddedMinter(_minter,msg.sender,block.timestamp,block.number);
        }
    }

    /**
    * @dev _removeMinter
    *      Internal function to remove minter role from an user.
    * @param _minter user address
    */
    function _removeMinter(address _minter) internal {
        RolesERC20 storage user = permissions[_minter];
        user.minter = false;
        emit RemovedMinter(_minter,msg.sender,block.timestamp,block.number);
        _SafeRemoveFromAuthERC20(_minter);
    }

    event AddedPaymentManager(
        address indexed user,
        address indexed signer,
        uint256 timestamp,
        uint256 blockNumber
    );
    event RemovedPaymentManager(
        address indexed user,
        address indexed signer,
        uint256 timestamp,
        uint256 blockNumber
    );

    /**
    * @dev _addPaymentManager
    *      Internal function to add paymentManager role to an user.
    * @param _paymentCollector user address
    */
    function _addPaymentManager(address _paymentCollector) internal {
        if(_paymentCollector != address(0)){
            RolesERC20 storage user = permissions[_paymentCollector];
            require(user.paymentManager == false, "ERC20Roles:  ALREADY A FEE MANAGER");
            user.paymentManager = true;
            _pushToAuthERC20(_paymentCollector);
            emit AddedPaymentManager(_paymentCollector,msg.sender,block.timestamp,block.number);
        }
    }

    /**
    * @dev _removePaymentManager
    *      Internal function to remove paymentManager role from an user.
    * @param _paymentCollector user address
    */
    function _removePaymentManager(address _paymentCollector) internal {
        RolesERC20 storage user = permissions[_paymentCollector];
        user.paymentManager = false;
        emit RemovedPaymentManager(_paymentCollector,msg.sender,block.timestamp,block.number);
        _SafeRemoveFromAuthERC20(_paymentCollector);
    }


    

   
    event CleanedPermissions(
        address indexed signer,
        uint256 timestamp,
        uint256 blockNumber
    );

    
    function _cleanPermissions() internal {
        
        for (uint256 i = 0; i < authERC20.length; i++) {
            RolesERC20 storage user = permissions[authERC20[i]];
            user.minter = false;
            user.paymentManager = false;

        }
        
        delete authERC20;
        emit CleanedPermissions(msg.sender,block.timestamp,block.number);
        
    }



        /**
    * @dev _pushToAuthERC20
    *      Checks authERC20 array and adds the user address if does not exists
    * @param user address to be checked
    */
    function _pushToAuthERC20(address user) internal {
        uint256 i;
        for (i = 0; i < authERC20.length; i++) {
            if(authERC20[i] == user) break;
        }
        if(i == authERC20.length){
            // element was not found
            authERC20.push(user);
        }
    }

    /**
    * @dev _SafeRemoveFromAuthERC20
    *      Checks if user has any roles left, and if not, it will remove it from auth array
    * @param user address to be checked and removed
    */
    function _SafeRemoveFromAuthERC20(address user) internal {
        RolesERC20 storage userRoles = permissions[user];
        if (userRoles.minter == false &&
            userRoles.paymentManager == false
        ){
            uint256 i;
            for (i = 0; i < authERC20.length; i++) {
                if(authERC20[i] == user) break;
            }
            if(i < authERC20.length){
                authERC20[i] = authERC20[authERC20.length -1];
                authERC20.pop();
            }
        }
    }
    
}
