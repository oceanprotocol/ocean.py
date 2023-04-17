pragma solidity 0.8.12;
// Copyright BigchainDB GmbH and Ocean Protocol contributors
// SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
// Code is Apache-2.0 and docs are CC-BY-4.0

contract ERC721RolesAddress {
    mapping(address => Roles) internal permissions;

    address[] public auth;

    struct Roles {
        bool manager;
        bool deployERC20;
        bool updateMetadata;
        bool store;
    }

    enum RolesType {
        Manager,
        DeployERC20,
        UpdateMetadata,
        Store
    }

    /**
    * @dev getPermissions
    *      Returns list of roles for an user
    * @param user user address
    */
    function getPermissions(address user) public view returns (Roles memory) {
        return permissions[user];
    }

     modifier onlyManager() {
        require(
            permissions[msg.sender].manager == true,
            "ERC721RolesAddress: NOT MANAGER"
        );
        _;
    }

    event AddedTo725StoreList(
        address indexed user,
        address indexed signer,
        uint256 timestamp,
        uint256 blockNumber
    );
    event RemovedFrom725StoreList(
        address indexed user,
        address indexed signer,
        uint256 timestamp,
        uint256 blockNumber
    );

    /**
    * @dev addTo725StoreList
    *      Adds store role to an user.
    *      It can be called only by a manager
    * @param _allowedAddress user address
    */
    function addTo725StoreList(address _allowedAddress) public onlyManager {
        if(_allowedAddress != address(0)){
            Roles storage user = permissions[_allowedAddress];
            user.store = true;
            _pushToAuth(_allowedAddress);
            emit AddedTo725StoreList(_allowedAddress,msg.sender,block.timestamp,block.number);
        }
    }

    /**
    * @dev removeFrom725StoreList
    *      Removes store role from an user.
    *      It can be called by a manager or by the same user, if he already has store role
    * @param _allowedAddress user address
    */
    function removeFrom725StoreList(address _allowedAddress) public {
        if(permissions[msg.sender].manager == true ||
        (msg.sender == _allowedAddress && permissions[msg.sender].store == true)
        ){
            Roles storage user = permissions[_allowedAddress];
            user.store = false;
            emit RemovedFrom725StoreList(_allowedAddress,msg.sender,block.timestamp,block.number);
            _SafeRemoveFromAuth(_allowedAddress);
        }
        else{
            revert("ERC721RolesAddress: Not enough permissions to remove from 725StoreList");
        }

    }


    event AddedToCreateERC20List(
        address indexed user,
        address indexed signer,
        uint256 timestamp,
        uint256 blockNumber
    );
    event RemovedFromCreateERC20List(
        address indexed user,
        address indexed signer,
        uint256 timestamp,
        uint256 blockNumber
    );

    /**
    * @dev addToCreateERC20List
    *      Adds deployERC20 role to an user.
    *      It can be called only by a manager
    * @param _allowedAddress user address
    */
    function addToCreateERC20List(address _allowedAddress) public onlyManager {
        _addToCreateERC20List(_allowedAddress);
    }

    //it's only called internally, so is without checking onlyManager
    function _addToCreateERC20List(address _allowedAddress) internal {
        Roles storage user = permissions[_allowedAddress];
        user.deployERC20 = true;
        _pushToAuth(_allowedAddress);
        emit AddedToCreateERC20List(_allowedAddress,msg.sender,block.timestamp,block.number);
    }

    /**
    * @dev removeFromCreateERC20List
    *      Removes deployERC20 role from an user.
    *      It can be called by a manager or by the same user, if he already has deployERC20 role
    * @param _allowedAddress user address
    */
    function removeFromCreateERC20List(address _allowedAddress)
        public
    {
        if(permissions[msg.sender].manager == true ||
        (msg.sender == _allowedAddress && permissions[msg.sender].deployERC20 == true)
        ){
            Roles storage user = permissions[_allowedAddress];
            user.deployERC20 = false;
            emit RemovedFromCreateERC20List(_allowedAddress,msg.sender,block.timestamp,block.number);
            _SafeRemoveFromAuth(_allowedAddress);
        }
        else{
            revert("ERC721RolesAddress: Not enough permissions to remove from ERC20List");
        }
    }

    event AddedToMetadataList(
        address indexed user,
        address indexed signer,
        uint256 timestamp,
        uint256 blockNumber
    );
    event RemovedFromMetadataList(
        address indexed user,
        address indexed signer,
        uint256 timestamp,
        uint256 blockNumber
    );

    /**
    * @dev addToMetadataList
    *      Adds metadata role to an user.
    *      It can be called only by a manager
    * @param _allowedAddress user address
    */
    function addToMetadataList(address _allowedAddress) public onlyManager {
        _addToMetadataList(_allowedAddress);
    }
    //it's only called internally, so is without checking onlyManager
    function _addToMetadataList(address _allowedAddress) internal {
        if(_allowedAddress != address(0)){
            Roles storage user = permissions[_allowedAddress];
            user.updateMetadata = true;
            _pushToAuth(_allowedAddress);
            emit AddedToMetadataList(_allowedAddress,msg.sender,block.timestamp,block.number);
        }
    }

    /**
    * @dev removeFromMetadataList
    *      Removes metadata role from an user.
    *      It can be called by a manager or by the same user, if he already has metadata role
    * @param _allowedAddress user address
    */
    function removeFromMetadataList(address _allowedAddress)
        public
    {
        if(permissions[msg.sender].manager == true ||
        (msg.sender == _allowedAddress && permissions[msg.sender].updateMetadata == true)
        ){
            Roles storage user = permissions[_allowedAddress];
            user.updateMetadata = false;    
            emit RemovedFromMetadataList(_allowedAddress,msg.sender,block.timestamp,block.number);
            _SafeRemoveFromAuth(_allowedAddress);
        }
        else{
            revert("ERC721RolesAddress: Not enough permissions to remove from metadata list");
        }
    }

    event AddedManager(
        address indexed user,
        address indexed signer,
        uint256 timestamp,
        uint256 blockNumber
    );
    event RemovedManager(
        address indexed user,
        address indexed signer,
        uint256 timestamp,
        uint256 blockNumber
    );

    /**
    * @dev _addManager
    *      Internal function to add manager role for an addres
    * @param _managerAddress user address
    */
    function _addManager(address _managerAddress) internal {
        if(_managerAddress != address(0)){
            Roles storage user = permissions[_managerAddress];
            user.manager = true;
            _pushToAuth(_managerAddress);
            emit AddedManager(_managerAddress,msg.sender,block.timestamp,block.number);
        }
    }

    /**
    * @dev _removeManager
    *      Internal function to clear the manager role for an addres
    * @param _managerAddress user address
    */
    function _removeManager(address _managerAddress) internal {
        Roles storage user = permissions[_managerAddress];
        user.manager = false;
        emit RemovedManager(_managerAddress,msg.sender,block.timestamp,block.number);
        _SafeRemoveFromAuth(_managerAddress);
    }


    event CleanedPermissions(
        address indexed signer,
        uint256 timestamp,
        uint256 blockNumber
    );

    /**
    * @dev _cleanPermissions
    *      Internal function to clear all existing permisions
    */
    function _cleanPermissions() internal {
        for (uint256 i = 0; i < auth.length; i++) {
            Roles storage user = permissions[auth[i]];
            user.manager = false;
            user.deployERC20 = false;
            user.updateMetadata = false;
            user.store = false;
        }

        delete auth;
        emit CleanedPermissions(msg.sender,block.timestamp,block.number);
    }

    /**
     * @dev addMultipleUsersToRoles
     *      Add multiple users to multiple roles
     * @param addresses Array of addresses
     * @param roles Array of coresponding roles
     */
    function addMultipleUsersToRoles(address[] memory addresses, RolesType[] memory roles) external onlyManager {
        require(addresses.length == roles.length && roles.length>0 && roles.length<50, "Invalid array size");
        uint256 i;
        for(i=0; i<roles.length; i++){
            if(addresses[i] != address(0)){
                Roles storage user = permissions[addresses[i]];
                if(roles[i] == RolesType.Manager) {
                    user.manager = true;
                    emit AddedManager(addresses[i],msg.sender,block.timestamp,block.number);
                }
                if(roles[i] == RolesType.DeployERC20) {
                    user.deployERC20 = true;
                    emit AddedToCreateERC20List(addresses[i],msg.sender,block.timestamp,block.number);
                }
                if(roles[i] == RolesType.UpdateMetadata) {
                    user.updateMetadata = true;
                    emit AddedToMetadataList(addresses[i],msg.sender,block.timestamp,block.number);
                }
                if(roles[i] == RolesType.Store) {
                    user.store = true;
                    emit AddedTo725StoreList(addresses[i],msg.sender,block.timestamp,block.number);
                }
                _pushToAuth(addresses[i]);
            }
        }
    }

    /**
    * @dev _pushToAuth
    *      Checks auth array and adds the user address if does not exists
    * @param user address to be checked
    */
    function _pushToAuth(address user) internal {
        uint256 i;
        for (i = 0; i < auth.length; i++) {
            if(auth[i] == user) break;
        }
        if(i == auth.length){
            // element was not found
            auth.push(user);
        }
    }

    /**
    * @dev _SafeRemoveFromAuth
    *      Checks if user has any roles left, and if not, it will remove it from auth array
    * @param user address to be checked and removed
    */
    function _SafeRemoveFromAuth(address user) internal {
        Roles storage userRoles = permissions[user];
        if (userRoles.manager == false &&
            userRoles.deployERC20 == false && 
            userRoles.updateMetadata == false &&
            userRoles.store == false
        ){
            uint256 i;
            for (i = 0; i < auth.length; i++) {
                if(auth[i] == user) break;
            }
            if(i < auth.length){
                auth[i] = auth[auth.length -1];
                auth.pop();
            }
        }
    }
}
