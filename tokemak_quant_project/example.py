import os

from dotenv import load_dotenv
from web3 import Web3
import helperFunctions as hf
import pandas as pd 

# https://github.com/ethers-io/ethers.js/blob/master/packages/providers/src.ts/alchemy-provider.ts#L16-L21
# NOTE: likely to get rate limited
default_provider_url = "https://eth-mainnet.g.alchemy.com/v2/_gg7wSSi0KMBsdKnGVfHDueq6xMB9EkC"

def main():
    load_dotenv()
    w3 = Web3(Web3.HTTPProvider(os.getenv('PROVIDER_URL', default_provider_url)))
    print(w3.eth.block_number)
        
    # Part 1. Collect, decode and store data for each pool.
    if True:
        if not os.path.exists("data/raw"):
            os.makedirs("data/raw")
        pools = hf.loadTopPools(w3)
        for pool in pools:
            print("Querying Swap Events for pool: ",pool)
            logs = hf.getSwapLogs(w3, pool)
            logs = hf.decodeSwapLogs(w3,pool,logs)
            hf.saveLogs(w3, logs, pool)
        print("Finished querying all data")
        
    # Part 2. Process the pool, calculate metrics etc.
    if True:
        pools = hf.loadTopPools(w3)
        metricTitle=['poolname','pool address','token0Symbol','token1Symbol','totalToken0Fee','totalToken1Fee','medianToken0Fee','medianToken1Fee','stdevToken0Fee','stdevToken1Fee', 'priceWETH', 'totalFeesWETH']
        metricRows=[]
        for pool in pools:
            print("Calculating metrics for pool: ",pool)
            swaps = hf.loadData(w3, pool)
            feesPerDayEst = hf.getFeesPerDayESTIMATE(swaps)    
            poolMetrics = hf.getPoolMetrics(w3, swaps, pool, feesPerDayEst)
            metricRows.append(poolMetrics)
        hf.saveMetricData(metricTitle,metricRows)
        print("Finished processed pool data to create metrics")
    
    # Part 3. Highlight top 10 pools
    print("Summary of top 10 pools - selected by total Fees denominated in WETH")
    df = pd.read_csv('data/pool_metric_data.csv')
    df = df.sort_values('totalFeesWETH',ascending=False)
    selected_pools = df.head(10)
    hf.saveSelectedPools(selected_pools)
    print(selected_pools)
    print("\nFile saved to data/selected_pools.csv")

if __name__ == '__main__':
    main()
