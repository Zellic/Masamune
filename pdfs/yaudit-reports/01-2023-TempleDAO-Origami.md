---
layout: default
title: 01-2023-TempleDao-Origami
description: TempleDAO Origami yAudit Report
nav_order: 17
image: assets/images/logo.png
---

yAudit TempleDAO Origami Review
===
{: .no_toc }

**Review Resources:**

- Some internal docs and visuals were provided

**Auditors:**

 - pandadefi
 - spalen
 - engn33r

## Table of Contents
{: .no_toc }

1. TOC
{:toc}

## Review Summary

**TempleDAO Origami**

The goal of TempleDAO's Origami product is to offer auto-compounded yield offerings on underlying strategies, maximising returns without sacrificing liquidity. The first strategy being offered is on [GLP and GMX](https://gmx.io/). Origami will be deployed on Arbitrum and Avalanche, the two chains where GMX is deployed, even though the current [Temple core contracts](https://docs.templedao.link/technical-reference/contracts) are deployed on Ethereum.

The contracts of the TempleDAO Origami [Repo](https://github.com/TempleDAO/origami) were reviewed over 21 days. The code review was performed by 3 auditors between January 23, 2023 and February 12, 2023. The repository was under active development during the review, but the review was limited to the latest commit at the start of the review. This was commit [a31d192ab54ca7d21f2dee30c630a6ec1843b646](https://github.com/TempleDAO/origami/tree/a31d192ab54ca7d21f2dee30c630a6ec1843b646/apps/protocol) for the TempleDAO repo.

## Scope

The scope of the review consisted of the files in the following directories at the specific commit:

- contracts/investments/*
- contracts/common/*

After the findings were presented to the TempleDAO team, fixes were made and included in several PRs.

This review is a code review to identify potential vulnerabilities in the code. The reviewers did not investigate security practices or operational security and assumed that privileged accounts could be trusted. The reviewers did not evaluate the security of the code relative to a standard or specification. The review may not have identified all potential attack vectors or areas of vulnerability.

yAudit and the auditors make no warranties regarding the security of the code and do not warrant that the code is free from defects. yAudit and the auditors do not represent nor imply to third parties that the code has been audited nor that the code is free from defects. By deploying or using the code, TempleDAO and users of the contracts agree to use the code at their own risk.


Code Evaluation Matrix
---

| Category                 | Mark    | Description |
| ------------------------ | ------- | ----------- |
| Access Control           | Average | Some privileged roles exist in the contracts, such as the Operator role and the CAN_MINT role. Many functions are protected by the onlyOwner modifier. |
| Mathematics              | Good | No complex math is performed in the contracts. Only basic accounting and value management is done. |
| Complexity               | Average | The complexity of the Temple Origami contracts were on par with a typical DeFi project. Some of the key functionalities included integration with a yield source (GMX), compounding of rewards, and custom tokens to track value. |
| Libraries                | Good | The only external dependencies are OpenZeppelin libraries. |
| Decentralization         | Average | The owner role has significant privileges in the Temple Origami contracts. The Operator and CAN_MINT roles are also privileged roles that may reduce the decentralization of the system. The `recoverToken()` function in many contracts indicates a high level of trust in the contract owner. |
| Code stability           | Average    | The code was nearly production ready but may not have been completely frozen prior to production deployment. |
| Documentation            | Good | Visuals were created to show the main user flows. Clear NatSpec comments existed throughout the contracts. |
| Monitoring               | Good | Events were emitted by all key functions that perform state variable changes. |
| Testing and verification | Low | The tests did not fully execute without errors so the extent of the test coverage could not be checked. |

## Findings Explanation

Findings are broken down into sections by their respective impact:
 - Critical, High, Medium, Low impact
     - These are findings that range from attacks that may cause loss of funds, impact control/ownership of the contracts, or cause any unintended consequences/actions that are outside the scope of the requirements
 - Gas savings
     - Findings that can improve the gas efficiency of the contracts
 - Informational
     - Findings including recommendations and best practices

---

## Critical Findings

None.

## High Findings

### 1. High - Harvesting vault can be front-run for profit

`sharesToReserves` increases immediately on profit distribution. A bad actor can sandwich the `harvestRewards()` call for immediate profit.

#### Technical Details

Calling [`harvestRewards()`](https://github.com/TempleDAO/origami/blob/a31d192ab54ca7d21f2dee30c630a6ec1843b646/apps/protocol/contracts/investments/gmx/OrigamiGmxRewardsAggregator.sol#L219) will collect and distribute rewards. A bad actor can deposit tokens into the ovToken before the harvest and withdraw from ovToken right after. The [`sharesToReserves`](https://github.com/TempleDAO/origami/blob/a31d192ab54ca7d21f2dee30c630a6ec1843b646/apps/protocol/contracts/common/RepricingToken.sol#L76) value will instantaneously increase and the attacker will be able to withdraw more tokens than deposited with reduced incentives for users to invest in the protocol in the future.

#### Impact

High. The protocol harvest call can be front-run, reducing the benefits for people invested in the protocol.

#### Recommendation

Distribute rewards over hours instead of immediate sharesToReserves increase.
One option is to keep a queue of rewards to distribute overtime. You can find an example in the [yearn vault](https://github.com/yearn/yearn-vaults/blob/master/contracts/Vault.vy#L831).

#### Developer Response

@frontier159: Fixed in [commit 8cbf5fb](https://github.com/TempleDAO/origami/commit/8cbf5fb65058fc4a5b3ca744d19737dc50177bfb)

The current vaults have a higher cost to enter/exit than what one would get by front-running. However point taken, and a good thing to address.

The plan to remediate is to add 'per second' distribution to users within the base `RepricingToken` contract. Summary (some detail left out for brevity):

1. When `addReserves()` is called, pull the reserve tokens from the caller
2. Those reserve tokens aren't immediately all available to users - it's dripped in per second.
3. So `totalReserves` then becomes a function instead of just a counter, effectively `return actualisedReserves + accruedReserves`
4. Whenever new reserves are added, we actualise:
   1. Any accrued up to now is added to `actualisedReserves`
   2. Any left over balance from the amount previously added is added to the new reserves being added
   3. The distribution timer restarts (set to block.timestamp)

We are planning on dripping the rewards in over a period of a week, and harvest daily. So each day the timer on the distribution will restart but the left over is carried over and the timer restarted.

## Medium Findings

### 1. Medium - `_handleGmxRewards()` returned values can lead to wrong accounting

When claiming GMX rewards, rewards come from GMX and GLP pools. The accounting can be wrong if the tokens claimed are staked.

#### Technical Details

The function [`_handleGmxRewards()`](https://github.com/TempleDAO/origami/blob/a31d192ab54ca7d21f2dee30c630a6ec1843b646/apps/protocol/contracts/investments/gmx/OrigamiGmxEarnAccount.sol#L387) calculates GMX rewards based on balance changes and claimable rewards from GLP without considering if the claimed tokens are staked.

When staking rewards, the code doesn't set to zero `esGmxFromGlp`. This is inconsistent with `esGmxFromGmx` computed using a balance change `esGmxFromGlp` and will be zero if rewards get staked.

[OrigamiGmxEarnAccount.sol#L396-L424](https://github.com/TempleDAO/origami/blob/a31d192ab54ca7d21f2dee30c630a6ec1843b646/apps/protocol/contracts/investments/gmx/OrigamiGmxEarnAccount.sol#L396-L424)

#### Impact

Medium. Inaccurate accounting may happen under certain circumstances.

#### Recommendation

Make sure to set `esGmxFromGlp` to zero when `shouldStakeEsGmx` is `true`.

#### Developer Response

@frontier159: Fixed in [commit fe96c8a](https://github.com/TempleDAO/origami/commit/fe96c8ab475a429bde242ffd62e0a946c06df705)

## Low Findings

### 1. Low - Use `glpRewardRouter` for fetching glp trackers

Initializer should use `glpRewardRouter` for fetching [GLP trackers](https://github.com/TempleDAO/origami/blob/a31d192ab54ca7d21f2dee30c630a6ec1843b646/apps/protocol/contracts/investments/gmx/OrigamiGmxEarnAccount.sol#L146-L147) but uses `gmxRewardRouter`.

#### Technical Details

Currently, both routers point to the same trackers, but this could change. Deployed [`glpRewardRouter`](https://arbiscan.io/address/0xB95DB5B167D75e6d04227CfFFA61069348d271F5#readContract#F15), for GMX trackers aren't set, points to address 0. The same could happen for `gmxRewardRouter`, GLP trackers could point to address 0.

#### Impact

Low. Trackers could be set to address 0 and break some contract functionalities.

#### Recommendation

Use values from `glpRewardRouter` for setting variables [`stakedGlpTracker`](https://github.com/TempleDAO/origami/blob/a31d192ab54ca7d21f2dee30c630a6ec1843b646/apps/protocol/contracts/investments/gmx/OrigamiGmxEarnAccount.sol#L146) and [`feeGlpTracker`](https://github.com/TempleDAO/origami/blob/a31d192ab54ca7d21f2dee30c630a6ec1843b646/apps/protocol/contracts/investments/gmx/OrigamiGmxEarnAccount.sol#L147).

```solidity
stakedGlpTracker = IGmxRewardTracker(glpRewardRouter.stakedGlpTracker());
feeGlpTracker = IGmxRewardTracker(glpRewardRouter.feeGlpTracker());
```

#### Developer Response

@frontier159: Fixed in [commit 5925173](https://github.com/TempleDAO/origami/commit/5925173da09fe63e3f8fc6ab50da6cb2f3068844)

### 2. Low - No Chainlink staleness check in `oraclePrice()`

`oraclePrice()` retrieves price data from Chainlink, but there are no checks to discard data if the oracle returns stale data.

#### Technical Details

The Chainlink `latestRoundData()` function returns price data along with the roundId and timestamp of the data. If the data is stale, it should be discarded. Otherwise the protocol will trust outdated data that could lead to a loss of value from using an inaccurate exchange rate. It is recommended to check the roundId and timestamp values that the oracle returns, as shown in other security report findings [here](https://consensys.net/diligence/audits/2021/09/fei-protocol-v2-phase-1/#chainlinkoraclewrapper---latestrounddata-might-return-stale-results) and [here](https://github.com/code-423n4/2021-05-fairside-findings/issues/70).

#### Impact

Low. The Chainlink oracle data should be checked for staleness.

#### Recommendation

Consider modifying `oraclePrice()` to the following:
```diff
	function oraclePrice(address _oracle) public view returns (uint256 price) {
        IAggregatorV3Interface oracle = IAggregatorV3Interface(_oracle);
-        (, int256 feedValue, , , ) = oracle.latestRoundData();
+        (uint80 roundId, int256 feedValue, , uint256 updatedAt, uint80 answeredInRound) = oracle.latestRoundData();
+		if (answeredInRound <= roundId && block.timestamp - updatedAt > ORACLE_STALENESS_THRESHOLD) revert InvalidPrice(feedValue);
        if (feedValue < 0) revert InvalidPrice(feedValue);
        price = scaleToPrecision(uint256(feedValue), oracle.decimals());
    }
```

#### Developer Response

@frontier159: Fixed in [commit 011c36d](https://github.com/TempleDAO/origami/commit/011c36df36d292e155e9c4cb34f2a29a92741f4d)

## Gas Savings Findings

### 1. Gas - Variables could be immutables

Some variables set on `OrigamiGmxEarnAccount` aren't likely to change. These variables can be set during contract creation and the variables can be declared immutable for gas savings.

#### Technical Details

[These variables](https://github.com/TempleDAO/origami/blob/a31d192ab54ca7d21f2dee30c630a6ec1843b646/apps/protocol/contracts/investments/gmx/OrigamiGmxEarnAccount.sol#L34-L40) can be declared immutable:

```solidity
/// @notice $GMX
IERC20Upgradeable public gmxToken; 

/// @notice $esGMX - escrowed GMX
IERC20Upgradeable public esGmxToken;

/// @notice $wrappedNative - wrapped ETH/AVAX
IERC20Upgradeable public wrappedNativeToken;
```

These three variables won't change. The contract constructor can set them appropriately.

#### Impact

Gas savings.

#### Recommendation

Declare these three variables as immutable. The contract constructor can take `gmxRewardRouter` to fetch the values.

#### Developer Response

@frontier159: Fixed in [commit 802f3c4](https://github.com/TempleDAO/origami/commit/802f3c4e16abb092c911a76192ba86f06d089684)

### 2. Gas - Initialize variable only if needed

In some cases where variables are initialized, the variables won't be used. This in inefficient and variables should only be initialized when they are used.

#### Technical Details

Variable [`esGmxReinvested`](https://github.com/TempleDAO/origami/blob/a31d192ab54ca7d21f2dee30c630a6ec1843b646/apps/protocol/contracts/investments/gmx/OrigamiGmxEarnAccount.sol#L341) is initialized before the if statement but it's only used inside the if block.

#### Impact

Gas savings.

#### Recommendation

Initialize variable [`esGmxReinvested`] inside the if block.

```diff
-  uint256 esGmxReinvested;
  if (totalEsGmxClaimed != 0) {
+      uint256 esGmxReinvested;
```

#### Developer Response

@frontier159: Fixed in [commit 2e575b3](https://github.com/TempleDAO/origami/commit/2e575b3d73327a75d9e5be6c65bb57bb6472749b)

### 3. Gas - Reuse local variable

Local variables can be reused instead of initializing new ones without losing code readability.

#### Technical Details

Variable [`fromToken`](https://github.com/TempleDAO/origami/blob/a31d192ab54ca7d21f2dee30c630a6ec1843b646/apps/protocol/contracts/investments/gmx/OrigamiGmxManager.sol#L528) can be reused instead of initializing the new variable `tokenIn`. The same applies to variable [`tokenOut`](https://github.com/TempleDAO/origami/blob/a31d192ab54ca7d21f2dee30c630a6ec1843b646/apps/protocol/contracts/investments/gmx/OrigamiGmxManager.sol#L610).

Local variable `reserveAmount` can be dropped from [here](https://github.com/TempleDAO/origami/blob/a31d192ab54ca7d21f2dee30c630a6ec1843b646/apps/protocol/contracts/investments/OrigamiInvestmentVault.sol#L314) and [here](https://github.com/TempleDAO/origami/blob/a31d192ab54ca7d21f2dee30c630a6ec1843b646/apps/protocol/contracts/investments/OrigamiInvestmentVault.sol#L352) if inline is used like this: `underlyingQuoteData.underlyingExitQuoteData.investmentTokenAmount = _redeemReservesFromShares`

#### Impact

Gas savings.

#### Recommendation

Reuse existing variables:

```diff
- address tokenOut = (toToken == address(0)) ? wrappedNativeToken : toToken;
+ toToken = (toToken == address(0)) ? wrappedNativeToken : toToken;
```

#### Developer Response

@frontier159: Fixed in [commit 8e2bd54](https://github.com/TempleDAO/origami/commit/8e2bd54111874bc062a29977d827f43de80b2214)

### 4. Gas - Use `msg.sender` not `owner()`

When two variables or function calls return equivalent values, it makes sense to use the option that uses less gas.

#### Technical Details

It is cheaper to call `msg.sender` instead of `ownable()` when they both return the same value. If this change is made [in the constructor of MintableToken](https://github.com/TempleDAO/origami/blob/a31d192ab54ca7d21f2dee30c630a6ec1843b646/apps/protocol/contracts/common/MintableToken.sol#L26), the range of gas used on the deployment of MintableToken is reduced from the original range of 2296764-2296884 to 2296354-2296474, saving roughly 400 gas.

#### Impact

Gas savings.

#### Recommendation

Replace `owner()` with `msg.sender` in the MintableToken constructor.

#### Developer Response

@frontier159: Fixed in [commit b538b51](https://github.com/TempleDAO/origami/commit/b538b51dfa75c4b178fd92ba44a4dc6d14e575b9)

## Informational Findings

### 1. Informational - Incorrect comment

The comment has an incorrect file name.

#### Technical Details

File OrigamiGmxInvestment has a [comment](https://github.com/TempleDAO/origami/blob/a31d192ab54ca7d21f2dee30c630a6ec1843b646/apps/protocol/contracts/investments/gmx/OrigamiGmxInvestment.sol#L3) with an incorrect file name.

#### Impact

Informational.

#### Recommendation

Update comment to correspond to the file name.

#### Developer Response

@frontier159: Fixed in [commit 7b78684](https://github.com/TempleDAO/origami/commit/7b786843726b7826ce8bf0c1324a22fb716a65fb)

### 2. Informational - Oracles price can be exploited

Two price oracles that are used for off-chain calculations can be manipulated. These oracles should never be used for on-chain calculations.

#### Technical Details

- [TokenPrices.sol#L74](https://github.com/TempleDAO/origami/blob/a31d192ab54ca7d21f2dee30c630a6ec1843b646/apps/protocol/contracts/common/TokenPrices.sol#L74): this price oracle can be exploited with a single block sandwich attack.

- [TokenPrices.sol#L85](https://github.com/TempleDAO/origami/blob/a31d192ab54ca7d21f2dee30c630a6ec1843b646/apps/protocol/contracts/common/TokenPrices.sol#L85): this price oracle can be exploited via a multi-block attack by block producers. [More info](https://uniswap.org/blog/what-to-know-pre-merge).

#### Impact

Informational.

#### Recommendation

Make sure not to use these two oracles from a smart contract.

#### Developer Response

@frontier159: Fixed in [commit fb002bf](https://github.com/TempleDAO/origami/commit/fb002bf6c14fca141544f93f464f33b50f938c94)

### 3. Informational - Update comment to NatSpec format

Some comments are written as NatSpec but are missing characters, including `/` and `@notice`, to be in the correct format.

#### Technical Details

In file [OrigamiGmxManager](https://github.com/TempleDAO/origami/blob/a31d192ab54ca7d21f2dee30c630a6ec1843b646/apps/protocol/contracts/investments/gmx/OrigamiGmxManager.sol) variables [`primaryEarnAccount`](https://github.com/TempleDAO/origami/blob/a31d192ab54ca7d21f2dee30c630a6ec1843b646/apps/protocol/contracts/investments/gmx/OrigamiGmxManager.sol#L78-L81) and [`secondaryEarnAccount`](https://github.com/TempleDAO/origami/blob/a31d192ab54ca7d21f2dee30c630a6ec1843b646/apps/protocol/contracts/investments/gmx/OrigamiGmxManager.sol#L83-L88) could be in NatSpec format.

At least two comments ([1](https://github.com/TempleDAO/origami/blob/a31d192ab54ca7d21f2dee30c630a6ec1843b646/apps/protocol/contracts/common/RepricingToken.sol#L75), [2](https://github.com/TempleDAO/origami/blob/a31d192ab54ca7d21f2dee30c630a6ec1843b646/apps/protocol/contracts/common/RepricingToken.sol#L85)) are missing the [@notice NatSpec tag](https://docs.soliditylang.org/en/latest/natspec-format.html#tags).

Finally, the comment on `reservesToShares()` is identical to the comment on `sharesToReserves()`, which is incorrect. The comment for `reservesToShares()` should be reversed to read "How many shares given a number of reserve tokens".

#### Impact

Informational.

#### Recommendation

Update comments to be in NatSpec format by adding missing characters.

#### Developer Response

@frontier159: Fixed in [commit 8be8c94](https://github.com/TempleDAO/origami/commit/8be8c948df35bcfb8ef8942ef7dc8317cd77ec43)

### 4. Informational - Verify fees and rewards addresses

The addresses for receiving fees and rewards can be set to address 0, so all fees and rewards could be lost.

#### Technical Details

Setter functions in OrigamiGmxManager for [`feeCollector`](https://github.com/TempleDAO/origami/blob/a31d192ab54ca7d21f2dee30c630a6ec1843b646/apps/protocol/contracts/investments/gmx/OrigamiGmxManager.sol#L188) and [rewards aggregators](https://github.com/TempleDAO/origami/blob/a31d192ab54ca7d21f2dee30c630a6ec1843b646/apps/protocol/contracts/investments/gmx/OrigamiGmxManager.sol#L208) doesn't verify input for the default 0 value. There are no checks to prevent an address of 0 when the fees and rewards are distributed.

#### Impact

Informational. Only the owner can set the addresses, so it is under the owner's control, but could lead to lost funds for protocol users.

#### Recommendation

Verify the addresses are not 0 before setting state variables and setting default values in the constructor, could use address(this). Another option is to keep fees and rewards in the OrigamiGmxManager if the address is not set and recover the token later.

#### Developer Response

@frontier159: Fixed in [commit 70dd257](https://github.com/TempleDAO/origami/commit/70dd257e1698cd42396bd4e80172b0f06d9ff840)

Won't fix checking in the constructor - we have robust checks on mainnet deploys, risk here is accepted.

### 5. Informational - Remove `removeReserves(uint256 amount)`

The function [`removeReserves(uint256 amount)`](https://github.com/TempleDAO/origami/blob/a31d192ab54ca7d21f2dee30c630a6ec1843b646/apps/protocol/contracts/common/RepricingToken.sol#L136) exposes a possibility to drain the protocol, but the function doesn't have a use case.

#### Technical Details

The function enables operators to take all `reserveToken` which can after be redeemed for other tokens depending on the OrigamiInvestment implementation. Even `recoverToken(address _token, address _to, uint256 _amount)` function, which is limited to only the owner, verifies the owner [cannot drain the protocol](https://github.com/TempleDAO/origami/blob/a31d192ab54ca7d21f2dee30c630a6ec1843b646/apps/protocol/contracts/common/RepricingToken.sol#L57).

#### Impact

Informational.

#### Recommendation

Remove the function.

#### Developer Response

@frontier159: Fixed in [commit 6ea7a6c](https://github.com/TempleDAO/origami/commit/6ea7a6c93087b7c87ba2c231a7f02f00c2f05113)

### 6. Informational - Trader Joe AMM is moving liquidity to a new AMM design

The Trader Joe AMM is moving liquidity to a new AMM design so it would benefit TokenPrices to use the newer AMM.

#### Technical Details

Trader Joe is used as a price oracle on [TokenPrices.sol#L74](https://github.com/TempleDAO/origami/blob/a31d192ab54ca7d21f2dee30c630a6ec1843b646/apps/protocol/contracts/common/TokenPrices.sol#L74). Trader Joe announced a new AMM design with breaking ABI changes. The [design](https://github.com/traderjoe-xyz/joe-v2/blob/main/src/LBFactory.sol#L244) will allow anyone, not just Trader Joe, to create new trading pools, so liquidity is expected to move to the new AMM.

- [announcement](https://medium.com/avalancheavax/trader-joe-presents-liquidity-book-a-new-amm-design-for-defi-39abf87e0d7f)
- [doc](https://docs.traderjoexyz.com/)

#### Impact

Informational.

#### Recommendation

Use the newer Trader Joe AMM. Replace `joePair.getReserves()` with `joePair.getReservesAndId()`.

#### Developer Response

@frontier159: Fixed in [commit d7499c8](https://github.com/TempleDAO/origami/commit/d7499c8ba5240bcddfcb45e34d95117eba55c1d2)

Now using the v2 helper to get the 'best' quote from all v1 and v2 pools.

### 7. Informational - Incorrect NatSpec

The Operators.sol contract has a NatSpec error.

#### Technical Details

On [Operators.sol#L19](https://github.com/TempleDAO/origami/blob/a31d192ab54ca7d21f2dee30c630a6ec1843b646/apps/protocol/contracts/common/access/Operators.sol#L19) `@dev` NatSpec specifies this `__Operators_init()` initializes the owner, but it's not initializing the owner.

#### Impact

Informational.

#### Recommendation

Update NatSpec in Operators.sol.

#### Developer Response

@frontier159: Fixed in [commit 65b27c6](https://github.com/TempleDAO/origami/commit/65b27c6776fc018652a9b7c1cc01cccd3c25bc89)

### 8. Informational - `addToReserveAmount` could be a percentage value

The `addToReserveAmount` uint256 value in `HarvestGmxParams` and `HarvestGlpParams` structures can be expressed as a percentage value for more precision.

#### Technical Details

In [`_compoundOvGmxRewards()`](https://github.com/TempleDAO/origami/blob/a31d192ab54ca7d21f2dee30c630a6ec1843b646/apps/protocol/contracts/investments/gmx/OrigamiGmxRewardsAggregator.sol#L234) and [`_compoundOvGlpRewards()`](https://github.com/TempleDAO/origami/blob/a31d192ab54ca7d21f2dee30c630a6ec1843b646/apps/protocol/contracts/investments/gmx/OrigamiGmxRewardsAggregator.sol#L253), the number of tokens to add to the reserve could be calculated using the returned value from `investWithToken()` and a percentage. This change would improve the precision of tokens added to the reserve, making it easier to send 100% of the rewards after slippage to the reserve.

#### Impact

Informational.

#### Recommendation

Use a percent-based approach using the return value from `investWithToken()`

#### Developer Response

@frontier159: Fixed in [commit 8cbf5fb](https://github.com/TempleDAO/origami/commit/8cbf5fb65058fc4a5b3ca744d19737dc50177bfb)

### 9. Informational - Replace deprecated dependency

MintableToken has a dependency of draft-ERC20Permit.sol, but this dependency is described by OpenZeppelin as deprecated.

#### Technical Details

[draft-ERC20Permit.sol](https://github.com/TempleDAO/origami/blob/a31d192ab54ca7d21f2dee30c630a6ec1843b646/apps/protocol/contracts/common/MintableToken.sol#L8) is the old file in @openzeppelin/contracts which has been replaced with ERC20Permit.sol. Remove the import of draft-ERC20Permit.sol and instead import ERC20Permit.sol.

A related simplification is the ERC20.sol dependency can be removed from MintableToken because it is already imported through ERC20Permit.sol.

#### Impact

Informational.

#### Recommendation

Import ERC20Permit.sol instead of draft-ERC20Permit.sol in MintableToken. Remove the ERC20.sol import from MintableToken.

#### Developer Response

@frontier159: Nothing to fix

This hasn't yet been released -- it will be in 4.9.*, where as the released version is 4.8.1

NB: `master` branch is their yet to be released version. See `release-v4.8` branch for the v4.8.* versions
ie: (https://github.com/OpenZeppelin/openzeppelin-contracts/tree/release-v4.8/contracts/token/ERC20/extensions)

### 10. Informational - Unusual Operator.sol implementation

The Operator.sol is implemented similar to an upgradeable contract from [openzeppelin-contracts-upgradeable](https://github.com/OpenZeppelin/openzeppelin-contracts-upgradeable), but it is used as a dependency in contracts that are not upgradeable. Only OrigamiGmxEarnAccount is an upgradeable contract behind a proxy, the other contracts that inherit Operator are not upgradeable.

#### Technical Details

The Operator.sol contract is implemented in the same pattern as contracts from openzeppelin-contracts-upgradeable. This includes inheriting Initializeable and having an init function. But unlike other OZ upgradeable contracts, the init functions in Operator.sol don't do anything. There is no difference in the contract if it is initialize or not.

A side effect of how this contract is used by other contracts is that every contract that inherits Operator.sol will have its own list of operators. If the intent is to manage only a single list of operators that have access to several different contracts, then consider deploying Operator.sol on its own, rather than as a dependency, and integrate it with the other contracts accordingly.

#### Impact

Informational.

#### Recommendation

Consider modifying Operator.sol to remove unnecessary artifacts borrowed from the openzeppelin-contracts-upgradeable pattern.

#### Developer Response

@frontier159: Fixed in [commit 65b27c6](https://github.com/TempleDAO/origami/commit/65b27c6776fc018652a9b7c1cc01cccd3c25bc89)

### 11. Informational - Reconsider using DEFAULT_ADMIN_ROLE

The DEFAULT_ADMIN_ROLE role in AccessControl is effectively a superuser role. It may make sense to avoid using this role if the goal is to make the contract more decentralized and less reliant on trusting a specific address.

#### Technical Details

[OpenZeppelin's documentation for DEFAULT_ADMIN_ROLE](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/5a00628ed3d6ce3154cee4d2cc93fad920e8ea30/contracts/access/AccessControl.sol#L45) warns that the role is effectively a superuser. If the only changing of roles is through `addMinter()` and `revokeRole()`, using DEFAULT_ADMIN_ROLE and importing AccessControl may be overkill. It could be simpler to maintain a mapping of addresses that have this access instead of inheriting the library.

Related to this, `addMinter()` and `removeMinter()` have duplicate modifiers. In the existing code, the caller must be the owner because of the modifier in MintableToken and the caller must be the adminRole because of the modifier in AccessControl. Consider removing the onlyOwner modifier to save gas.

#### Impact

Informational.

#### Recommendation

Remove the onlyOwner modifier to save gas. Consider whether inheriting AccessControl is necessary at all or whether using a local mapping of addresses that can mint is a viable replacement.

#### Developer Response

@frontier159: Fixed in [commit b538b51](https://github.com/TempleDAO/origami/commit/b538b51dfa75c4b178fd92ba44a4dc6d14e575b9)

### 12. Informational - Consider zero for minAmount

`mintAndStakeGlp()` in OrigamiGmxEarnAccount has two minAmount arguments. One of these can be removed and a zero value passed to `glpRewardRouter.mintAndStakeGlp()`.

#### Technical Details

`glpRewardRouter.mintAndStakeGlp()` has two minAmount arguments. Only one of these is really necessary. Consider removing the other and replacing it with a zero minAmount depending on the standard use case for the `mintAndStakeGlp()` function.

#### Impact

Informational.

#### Recommendation

Remove the `minUsdg` or `minGlp` argument from `mintAndStakeGlp()` and pass a zero minAmount instead of this value.

#### Developer Response

@frontier159: Fixed in [commit a2037d8](https://github.com/TempleDAO/origami/commit/a2037d89bcfde599dd2eeb43cdd8f70720a8c4df)

### 13. Informational - Broken link

There is a broken link in a comment.

#### Technical Details

TokenPrices.sol links to https://docs.uniswap.org/sdk/guides/fetching-prices which returns Page Not Found. Consider linking to the archived page https://web.archive.org/web/20210918154903/https://docs.uniswap.org/sdk/guides/fetching-prices.

#### Impact

Informational.

#### Recommendation

Fix the broken link.

#### Developer Response

@frontier159: Fixed in [commit 8be8c94](https://github.com/TempleDAO/origami/commit/8be8c948df35bcfb8ef8942ef7dc8317cd77ec43)

### 14. Informational - Typo

At least one comment has a typo.

#### Technical Details

[adggregator](https://github.com/TempleDAO/origami/blob/a31d192ab54ca7d21f2dee30c630a6ec1843b646/apps/protocol/contracts/investments/gmx/OrigamiGmxRewardsAggregator.sol#L183) -> aggregator

#### Impact

Informational.

#### Recommendation

Fix typos.

#### Developer Response

@frontier159: Fixed in [commit 4a8c036](https://github.com/TempleDAO/origami/commit/4a8c0365955e263628ff84ee4a99e1ddd6859ea3)

## Final remarks

### spalen

In summary, complexity should be reduced to enhance security, and some aspects of Origami may benefit from refactoring to simplify the overall design. For example, the flow of depositing and withdrawing is split into multiple steps between different contracts. The process starts with the vault to invest funds, then value flows to the manager, and it ends up in the earn account. The flow is complex and guarded by operators, but there are potential problems in the withdrawal process if there are malicious operators. There are several withdrawal functions that could remove significant value from the protocol, found in the earn account contract function, unstake GMX, and in manager contract. Finally, the earn account contract is upgradeable and holds all assets, which puts a lot of faith in the protocol owners. This can be mitigated by providing a clear upgrade procedure with a timelock and limiting the contract operators.

### pandadefi

No critical risks were found. The code is well structured allowing it to be future-proof to follow GMX possible changes. Some of the profit distribution mechanism needs to be rethought to prevent exploits. There is a large number of functions with protected access, and operating those will require caution.

### engn33r

Integrations with GMX are usually a bit more complex that older DeFi protocols because of the different tokens and contracts involved, and this case is no different. Because GMX is dynamic and has frequent changes, like the removal of some cooldown parameters a few months ago, integrations with GMX must be designed for adaptation. The choice to use a custom vault that is not ERC4626 compliant is a bit unusual these days, but the vault appears to do its job properly so it doesn't matter much. Providing a token to compound GMX rewards while abstracting away the complexity of the protocol has the potential for use cases even outside of the TEMPLE token.
