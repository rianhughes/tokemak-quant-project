
## To run the code:

From the root folder execute:
poetry run python3.10 tokemak_quant_project/example.py

Also, note: I added my own Alchemy API Key as a default in the main file, as the previous one was heavily rate limited. While I normally use an .env file for these things, I added it here for the ease of checking this code.

## Outline of project

### Part 1: Collect, decode and store data
1. I selected the top 10 pools on uniswap that involve WETH by hand, and saved them into data/list_of_top_weth_pools.csv. This was done instead of using the uni_v2_sushi_pools.csv data to speed things up (in practice could filter uni_v2_sushi_pools.csv by reserves etc).
2. For each pool, call eth_getLogs() while filtering by the Swap hash. 
3. Decode the response
4. Save the data. Each pool data gets its own file in data/raw/data_[pool_address]_.json

### Part 2: Process data
To rank the pools we need to calculate the fees they have collected over time. 
1. Process the swap logs for each pool, to calculate the fees collected in token0 and token1 over time.
2. Use this fee vs time data to calculate metrics.
3. The metrics I choose were total fees collected in each token, median token fee, and standard-deviation of the token fee. I also used the latest swap log to calculate the non-WETH to WETH price.
4. The ultimate metric I used to rank the pools was the total fees collected in WETH. This required calculating the nonWETH-WETH price, which I did use the latest swap log.
5. Save a table (data/pool_metric_data.csv) of the metrics calculated for each pool. Note that the fees account for each token's decimals etc.

### Part 3: Select the top 10 pool.
I used the total fees, denominated in WETH, to rank the pools the select the top 10 pools.
This data was then stored in data/selected_pools.csv

## Metrics:

The main metric that I used was the total fees accrued by the pool, denominated in WETH. This seems like a decent metric to initially rank the different pools, given it is a common asset between all pairs. However, in practice, one should really consider the price volatility of the non-WETH asset, as some of the pools considered here had relatively unknown tokens, whose price may become negligible relatively quickly. Of course, if one is interested in denominating their returns in USD, then the price movements of WETH should also be considered. 

The returns here should also really be weighted by TVL, since the fees are split across all Liquidity Providers.

To get a more realistic view of the pools, one should run the same program across the full data set 'uni_v2_sushi_pools.csv' (with some filtering if runtimes become a problem), across the entire lifetime of the pool. Short timeframes were used here for the sake of optimising for low runtimes.

Another metric that one should really consider is the stability of the returns, particularly the amount of time the pool isn't generating any fees. As such, one could rank pools by the median return. The volatility of returns is also a useful metric, as short periods of large volumes can generate high fees and returns.

## Additional Notes / Short-cuts:

To save time the following assumptions were made:
1. I only gathered recent data. This can be changed using the local variable 'startTime' in helperFunctions.getSwapLogs()
2. I assume that all non-WETH tokens were converted into WETH using the current price, rather than daily, etc.
3. I only look at the performance of the pool, and not the returns a portfolio would get. This requires accounting for TVL (as you only get a cut of the fees), etc.
4. I rank pools by the total WETH-denominated tokens they accumulate. In practice, one should also consider the stability of returns (variance), the price exposure to the non-WETH token, etc. 
5. I also implicitly assume we want to hold WETH. If the returns should be denominated in USD, one should consider WETH-based price exposure etc.
6. Some Uniswap pools are also 'attacked' (JIT liquidity, hackers drain pools (eg consider WETH-TINU)), and these risks haven't been accounted for, etc.

