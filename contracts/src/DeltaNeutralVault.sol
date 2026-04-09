// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IERC20Like {
    function balanceOf(address account) external view returns (uint256);
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
}

contract DeltaNeutralVault {
    string public constant SHARE_NAME = "Delta Neutral Vault Share";
    string public constant SHARE_SYMBOL = "DNVS";

    address public immutable asset;
    address public owner;
    bool public paused;

    uint256 public totalShares;
    uint256 public navAssets;

    mapping(address => uint256) public shareBalance;

    event Deposit(address indexed caller, address indexed receiver, uint256 assets, uint256 shares);
    event Withdraw(address indexed caller, address indexed receiver, uint256 assets, uint256 shares);
    event NavUpdated(uint256 previousNav, uint256 newNav, string note);
    event PauseUpdated(bool paused);
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    modifier onlyOwner() {
        require(msg.sender == owner, "not owner");
        _;
    }

    modifier whenNotPaused() {
        require(!paused, "vault paused");
        _;
    }

    constructor(address asset_) {
        require(asset_ != address(0), "invalid asset");
        asset = asset_;
        owner = msg.sender;
        emit OwnershipTransferred(address(0), msg.sender);
    }

    function totalAssets() external view returns (uint256) {
        return navAssets;
    }

    function previewDeposit(uint256 assets) public view returns (uint256 shares) {
        require(assets > 0, "zero assets");
        if (totalShares == 0 || navAssets == 0) {
            return assets;
        }
        return (assets * totalShares) / navAssets;
    }

    function previewWithdraw(uint256 assets) public view returns (uint256 shares) {
        require(assets > 0, "zero assets");
        require(totalShares > 0 && navAssets > 0, "empty vault");
        return _ceilDiv(assets * totalShares, navAssets);
    }

    function deposit(uint256 assets, address receiver) external whenNotPaused returns (uint256 shares) {
        require(receiver != address(0), "invalid receiver");
        shares = previewDeposit(assets);
        require(shares > 0, "zero shares");

        bool success = IERC20Like(asset).transferFrom(msg.sender, address(this), assets);
        require(success, "transfer failed");

        shareBalance[receiver] += shares;
        totalShares += shares;
        navAssets += assets;

        emit Deposit(msg.sender, receiver, assets, shares);
    }

    function withdraw(uint256 assets, address receiver) external whenNotPaused returns (uint256 shares) {
        require(receiver != address(0), "invalid receiver");
        shares = previewWithdraw(assets);
        require(shareBalance[msg.sender] >= shares, "insufficient shares");
        require(navAssets >= assets, "insufficient nav");

        shareBalance[msg.sender] -= shares;
        totalShares -= shares;
        navAssets -= assets;

        bool success = IERC20Like(asset).transfer(receiver, assets);
        require(success, "transfer failed");

        emit Withdraw(msg.sender, receiver, assets, shares);
    }

    function updateNav(uint256 newNav, string calldata note) external onlyOwner {
        uint256 previous = navAssets;
        navAssets = newNav;
        emit NavUpdated(previous, newNav, note);
    }

    function setPaused(bool shouldPause) external onlyOwner {
        paused = shouldPause;
        emit PauseUpdated(shouldPause);
    }

    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "invalid owner");
        address previousOwner = owner;
        owner = newOwner;
        emit OwnershipTransferred(previousOwner, newOwner);
    }

    function reportedCashBalance() external view returns (uint256) {
        return IERC20Like(asset).balanceOf(address(this));
    }

    function _ceilDiv(uint256 a, uint256 b) internal pure returns (uint256) {
        return a == 0 ? 0 : ((a - 1) / b) + 1;
    }
}

