pragma solidity 0.8.12;
// Copyright BigchainDB GmbH and Ocean Protocol contributors
// SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
// Code is Apache-2.0 and docs are CC-BY-4.0

import "../interfaces/IERC721Template.sol";
import "../interfaces/IERC20Template.sol";
import "../interfaces/IFactoryRouter.sol";
import "../interfaces/IFixedRateExchange.sol";
import "../interfaces/IDispenser.sol";
import "./ERC20Template.sol";
import "../utils/ERC20Roles.sol";

/**
 * @title DatatokenTemplate
 *
 * @dev DatatokenTemplate is an ERC20 compliant token template
 *      Used by the factory contract as a bytecode reference to
 *      deploy new Datatokens.
 */
contract ERC20Template3 is ERC20Template {
    using SafeERC20 for IERC20;

    mapping(uint256 => mapping(address => Prediction)) predobjs; // id to prediction object
    mapping(uint256 => uint256) predcounter; // block num to id counter
    mapping(uint256 => uint256) agg_predvals_numer;
    mapping(uint256 => uint256) agg_predvals_denom;
    mapping(uint256 => bool) truevals;

    uint256 blocks_per_epoch;
    uint256 blocks_per_subscription;
    uint256 min_predns_for_payout;
    address stake_token;

    constructor(
        uint256 s_per_block,
        uint256 s_per_epoch,
        uint256 s_per_subscription,
        uint256 _min_predns_for_payout,
        address _stake_token
    ) {
        min_predns_for_payout = _min_predns_for_payout;
        stake_token = _stake_token;

        require(s_per_subscription % s_per_block == 0, "must be divisible");
        require(s_per_epoch % s_per_block == 0, "must be divisible");

        blocks_per_epoch = s_per_epoch / s_per_block;
        blocks_per_subscription = s_per_subscription / s_per_block;
    }

    struct Prediction {
        bool predval;
        uint256 stake;
        address predictoor;
        bool paid;
    }

    // ----------------------- VIEW FUNCTIONS -----------------------

    /**
     * @dev getId
     *      Return template id in case we need different ABIs.
     *      If you construct your own template, please make sure to change the hardcoded value
     */
    function getId() public pure virtual override returns (uint8) {
        return 1;
    }

    function epoch() public view returns (uint256) {
        return block.number / blocks_per_epoch;
    }

    function rail_blocknum_to_slot(
        uint256 blocknum
    ) public view returns (uint256) {
        return (block.number / blocks_per_epoch) * blocks_per_epoch;
    }

    function blocknum_is_on_a_slot(
        uint256 blocknum
    ) public view returns (bool) {
        // a slot == beginning/end of an epoch
        return blocknum == rail_blocknum_to_slot(blocknum);
    }

    function soonest_block_to_predict() public view returns (uint256) {
        uint256 slotted_blocknum = rail_blocknum_to_slot(block.number);

        uint256 _blocknum;
        if (slotted_blocknum == block.number) {
            _blocknum = slotted_blocknum + blocks_per_epoch;
        } else {
            _blocknum = slotted_blocknum + 2 * blocks_per_epoch;
        }
        require(blocknum_is_on_a_slot(_blocknum), "blocknum must be on a slot");
        return _blocknum;
    }

    function submitted_predval(
        uint256 blocknum,
        address predictoor
    ) public view returns (bool) {
        require(blocknum_is_on_a_slot(blocknum), "blocknum must be on a slot");
        return predobjs[blocknum][predictoor].predictoor != address(0);
    }

    function get_agg_predval(
        uint256 blocknum
    ) public view returns (uint256, uint256) {
        require(blocknum_is_on_a_slot(blocknum), "blocknum must be on a slot");
        return (agg_predvals_numer[blocknum], agg_predvals_denom[blocknum]);
    }

    function _subscription_revenue_at_block(
        uint256 blocknum
    ) public view returns (uint256) {
        require(blocknum_is_on_a_slot(blocknum), "blocknum must be on a slot");
        // TODO
    }

    // ----------------------- MUTATING FUNCTIONS -----------------------

    function submit_predval(
        bool predval,
        uint256 stake,
        uint256 blocknum
    ) external {
        require(blocknum_is_on_a_slot(blocknum), "blocknum must be on a slot");
        require(blocknum > soonest_block_to_predict(), "too late to submit");
        require(!submitted_predval(blocknum, msg.sender), "already submitted");

        Prediction memory predobj = Prediction(
            predval,
            stake,
            msg.sender,
            false
        );

        predobjs[blocknum][msg.sender] = predobj;

        // safe transfer stake
        IERC20(stake_token).safeTransferFrom(msg.sender, address(this), stake);

        // update agg_predvals
        agg_predvals_numer[blocknum] += stake * (predval ? 1 : 0);
        agg_predvals_denom[blocknum] += stake;
    }

    function submit_trueval(
        uint256 blocknum,
        bool trueval
    ) external onlyERC20Deployer {
        // TODO, is onlyERC20Deployer the right modifier?
        require(blocknum_is_on_a_slot(blocknum), "blocknum must be on a slot");
        require(blocknum < soonest_block_to_predict(), "too early to submit");
        truevals[blocknum] = trueval;
    }

    function start_subscription() external {
        //TODO
    }

    function payout(uint256 blocknum, address predictoor_addr) external {
        require(blocknum_is_on_a_slot(blocknum), "blocknum must be on a slot");
        Prediction memory predobj = predobjs[blocknum][predictoor_addr];
        require(predobj.paid == false, "already paid");

        require(truevals[blocknum] == predobj.predval, "wrong prediction");

        uint256 swe = truevals[blocknum]
            ? agg_predvals_numer[blocknum]
            : agg_predvals_denom[blocknum] - agg_predvals_numer[blocknum];
        uint256 payout_amt = (predobj.stake *
            agg_predvals_denom[blocknum] *
            _subscription_revenue_at_block(blocknum)) / swe;

        // TODO SELL DTS TO TOP UP OCEAN BALANCE OF THE CONTRACT

        IERC20(stake_token).safeTransferFrom(
            address(this),
            predobj.predictoor,
            payout_amt
        );
        predobj.paid = true;
    }
}
