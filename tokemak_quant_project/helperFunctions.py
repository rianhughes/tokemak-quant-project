import csv
import json 
import statistics as stats
import matplotlib.pyplot as plt

## Collect and dcode data
def getSwapLogs(w3, pool_address):    
    logs = []
    startTime   = 16600000  # 16000000
    endTime     = 16622743  # 16622743
    timeStep    =     2000   # k needed so there is no cap on the size of the response
    time = startTime
    while time < endTime:
        logs.append(w3.eth.get_logs({'fromBlock': time,   'toBlock': time+timeStep,   'address': w3.toChecksumAddress(pool_address), 'topics' :["0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822"]}))
        time+=timeStep
    # Flatten logs        
    flat_logs = []
    for a in logs:
        for b in a:
            flat_logs.append(b)
    return flat_logs

def logToDict(log):
    dict = {}
    dict['args'] = {'sender' :       log['args']['sender'],
                   'to'     :       log['args']['to'],
                   'amount0In':     log['args']['amount0In'],
                   'amount1In':     log['args']['amount1In'],
                   'amount0Out' :   log['args']['amount0Out'],
                   'amount1Out' :   log['args']['amount1Out']
                   }
    dict['event'] = log['event']
    dict['blockHash']  = log['blockHash'].hex()
    dict['blockNumber'] = log['blockNumber']
    dict['transactionHash'] = log['transactionHash'].hex()
    dict['address'] = log['address']
    return dict

def logsToJson(logs):
    logAr = []
    for log in logs:
        logAr.append(logToDict(log))
    return logAr

def saveLogs(w3, logs, pool_address):
    
    logs = logsToJson(logs)
    pool_address = w3.toChecksumAddress(pool_address)
    
    with open('data/raw/data_' + pool_address + '_.json', 'w') as f:
        json.dump(logs, f)
    

## Evaluate pools

def getFeesPerDayESTIMATE(swaps):
    '''
    feesPerDayEst = [dayInd, blockNumber, agg0Swap*fee*decimals, agg1Swap*fee*decimals]
    Assumes there are 6645 blocks each day   
    '''
    fee = 0.3/100
    decimals = 10**-18
    blocksPerDay = 6645
    firstBlock = swaps[0]['blockNumber']

    dayInd = 0
    agg0Swap, agg1Swap = 0, 0
    feesPerDayEst = []
    for i in range(len(swaps)):
        curBlock = swaps[i]['blockNumber']       
        # print(agg0Swap, agg1Swap)
        # print("-",swaps[i]['args']['amount0In'],swaps[i]['args']['amount0Out'])
        # print("-",swaps[i]['args']['amount1In'],swaps[i]['args']['amount1Out'])
        
        # Fee on input token0 (neglect cases where both inputs are non-zero)
        if swaps[i]['args']['amount0In']==0:
            agg1Swap += abs(swaps[i]['args']['amount1In'] - swaps[i]['args']['amount1Out'])*fee*decimals  
        elif swaps[i]['args']['amount1In']==0:
            agg0Swap += abs(swaps[i]['args']['amount0In'] - swaps[i]['args']['amount0Out'])*fee*decimals  
                
        # new day, reset aggregates
        if curBlock >  dayInd*blocksPerDay + firstBlock:
            feesPerDayEst.append([dayInd, curBlock, agg0Swap, agg1Swap])    
            dayInd+=1
            agg0Swap, agg1Swap = 0, 0

    
    return feesPerDayEst

def saveFeesPerBlockTime(data,pool_address):
    with open('data/processed/data_' + pool_address + '_.json', 'w') as f:
        json.dump(data, f)

def plotFeesPerBlock(feesPerDayEst, pool_address):
    firstBlock = feesPerDayEst[0][1]
    y = [swap[0]  for swap in feesPerDayEst]
    xT0 = [swap[2] for swap in feesPerDayEst]
    xT1 = [swap[3] for swap in feesPerDayEst]
    print("sum",sum(xT0),sum(xT1))
    fig = plt.figure()
    fig.suptitle("Fees/Day \n"+ pool_address, fontsize=12)
    
    plt.subplot(1, 2, 1) 
    plt.plot(y,xT0)
    plt.ylabel('Fees token0')
    plt.xlabel('Time ( ~ #days since '+str(firstBlock)+')')
    plt.subplot(1, 2, 2) 
    plt.plot(y,xT1)
    plt.ylabel('Fees token1')
    plt.xlabel('Time (~ #days since '+str(firstBlock)+')')
    plt.show()

def getPoolMetrics(w3, swaps, pool_address, feesPerDayEst):
    # Total Fees
    # Median Fees per day
    # StdDev of Fees
    # USD value (if sold per day excl fees)
    # USD value if held and sold now
    
    # Get pool token symbols
    poolabi = '[{"inputs":[],"payable":false,"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"spender","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"sender","type":"address"},{"indexed":false,"internalType":"uint256","name":"amount0","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"amount1","type":"uint256"},{"indexed":true,"internalType":"address","name":"to","type":"address"}],"name":"Burn","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"sender","type":"address"},{"indexed":false,"internalType":"uint256","name":"amount0","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"amount1","type":"uint256"}],"name":"Mint","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"sender","type":"address"},{"indexed":false,"internalType":"uint256","name":"amount0In","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"amount1In","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"amount0Out","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"amount1Out","type":"uint256"},{"indexed":true,"internalType":"address","name":"to","type":"address"}],"name":"Swap","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"uint112","name":"reserve0","type":"uint112"},{"indexed":false,"internalType":"uint112","name":"reserve1","type":"uint112"}],"name":"Sync","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Transfer","type":"event"},{"constant":true,"inputs":[],"name":"DOMAIN_SEPARATOR","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"MINIMUM_LIQUIDITY","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"PERMIT_TYPEHASH","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"to","type":"address"}],"name":"burn","outputs":[{"internalType":"uint256","name":"amount0","type":"uint256"},{"internalType":"uint256","name":"amount1","type":"uint256"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"factory","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"getReserves","outputs":[{"internalType":"uint112","name":"_reserve0","type":"uint112"},{"internalType":"uint112","name":"_reserve1","type":"uint112"},{"internalType":"uint32","name":"_blockTimestampLast","type":"uint32"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"_token0","type":"address"},{"internalType":"address","name":"_token1","type":"address"}],"name":"initialize","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"kLast","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"to","type":"address"}],"name":"mint","outputs":[{"internalType":"uint256","name":"liquidity","type":"uint256"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"nonces","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"permit","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"price0CumulativeLast","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"price1CumulativeLast","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"to","type":"address"}],"name":"skim","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"uint256","name":"amount0Out","type":"uint256"},{"internalType":"uint256","name":"amount1Out","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"swap","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[],"name":"sync","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"token0","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"token1","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"}],"name":"transfer","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"}],"name":"transferFrom","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"}]'
    poolContract = w3.eth.contract(address=pool_address, abi=poolabi)
    token0Address = poolContract.functions.token0().call()
    token1Address = poolContract.functions.token1().call()
    
    tokenabi = '[{"inputs":[{"internalType":"uint256","name":"chainId_","type":"uint256"}],"payable":false,"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"src","type":"address"},{"indexed":true,"internalType":"address","name":"guy","type":"address"},{"indexed":false,"internalType":"uint256","name":"wad","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":true,"inputs":[{"indexed":true,"internalType":"bytes4","name":"sig","type":"bytes4"},{"indexed":true,"internalType":"address","name":"usr","type":"address"},{"indexed":true,"internalType":"bytes32","name":"arg1","type":"bytes32"},{"indexed":true,"internalType":"bytes32","name":"arg2","type":"bytes32"},{"indexed":false,"internalType":"bytes","name":"data","type":"bytes"}],"name":"LogNote","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"src","type":"address"},{"indexed":true,"internalType":"address","name":"dst","type":"address"},{"indexed":false,"internalType":"uint256","name":"wad","type":"uint256"}],"name":"Transfer","type":"event"},{"constant":true,"inputs":[],"name":"DOMAIN_SEPARATOR","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"PERMIT_TYPEHASH","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"usr","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"usr","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"burn","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"guy","type":"address"}],"name":"deny","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"usr","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"mint","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"src","type":"address"},{"internalType":"address","name":"dst","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"move","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"nonces","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"holder","type":"address"},{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"nonce","type":"uint256"},{"internalType":"uint256","name":"expiry","type":"uint256"},{"internalType":"bool","name":"allowed","type":"bool"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"permit","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"usr","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"pull","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"usr","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"push","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"guy","type":"address"}],"name":"rely","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"dst","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"transfer","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"src","type":"address"},{"internalType":"address","name":"dst","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"transferFrom","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"version","outputs":[{"internalType":"string","name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"wards","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"}]'
    token0Contract = w3.eth.contract(address=token0Address, abi=tokenabi)
    token1Contract = w3.eth.contract(address=token1Address, abi=tokenabi)
    token0Symbol = token0Contract.functions.symbol().call()
    token1Symbol = token1Contract.functions.symbol().call()
    token0Decimals= token0Contract.functions.decimals().call()
    token1Decimals = token1Contract.functions.decimals().call()

    # Uniswap deicla is 18, but some tokens have decimal of 6 (eg USDC). Need to account for this.
    decimal0Offset = 10**(18-token0Decimals)
    decimal1Offset = 10**(18-token1Decimals)

    # Calculate metrics to rank pools    
    token0DailyFees = [fee[2]*decimal0Offset for fee in feesPerDayEst]
    token1DailyFees = [fee[3]*decimal1Offset for fee in feesPerDayEst]
    
    
    totalToken0Fee = sum(token0DailyFees)
    totalToken1Fee = sum(token1DailyFees)
    medianToken0Fee = stats.median(token0DailyFees)
    medianToken1Fee = stats.median(token1DailyFees)
    stdevToken0Fee = stats.stdev(token0DailyFees)
    stdevToken1Fee = stats.stdev(token1DailyFees)
    
     # Get price and convert rewards to WETH
    priceWETH = getPriceFromSwap(swaps[-1],token0Decimals,token1Decimals, token0Symbol)
    #print("- priceWETH",priceWETH)
    totalFeesWETH = getTotalFeesInWETH(totalToken0Fee, totalToken1Fee, token0Symbol, priceWETH)
    
    
    
    poolname = 'UniV2-' + token0Symbol + '-' + token1Symbol
    #columns=['poolname','pool address','token0Symbol','token1Symbol','totalToken0Fee','totalToken1Fee','medianToken0Fee','medianToken1Fee','stdevToken0Fee','stdevToken1Fee','priceWETH', 'totalFeesWETH']
    data = [poolname,  pool_address,  token0Symbol,  token1Symbol,  totalToken0Fee,  totalToken1Fee,  medianToken0Fee,  medianToken1Fee,  stdevToken0Fee,  stdevToken1Fee,priceWETH, totalFeesWETH]
    return data

def getTotalFeesInWETH(totalToken0Fee, totalToken1Fee, token0Symbol, priceWETH):
    if priceWETH==None:
        return 0
        
    if token0Symbol=='WETH':
        return totalToken0Fee + totalToken1Fee/priceWETH
    else:
        return totalToken0Fee/priceWETH + totalToken1Fee
    

def getPriceFromSwap(swap, token0Decimals, token1Decimals, token0Symbol):
    amt0In = swap['args']['amount0In']*(10**-token0Decimals)
    amt1In = swap['args']['amount1In']*(10**-token1Decimals)
    amt0Out = swap['args']['amount0Out']*(10**-token0Decimals)
    amt1Out = swap['args']['amount1Out']*(10**-token1Decimals)
    # print(amt0In,amt1In,amt0Out,amt1Out)
    # print(swap['args'])
    # print(" - ",token0Symbol)

    if token0Symbol=='WETH':    
        if amt0In==0:
            return amt1In/amt0Out
        elif amt1In==0:
            return amt1Out/amt0In
    else:
        if amt0In==0:
            return amt0Out/amt1In
        elif amt1In==0:
            return amt0In/amt1Out
    
def saveMetricData(metricTitle,metricRows):
    with open("data/pool_metric_data.csv", "w") as fp:
        writer = csv.writer(fp, delimiter=",")
        
        writer.writerow(metricTitle)
        writer.writerows(metricRows)
        

def saveSelectedPools(selected_pools):
    selected_pools.to_csv("data/selected_pools.csv")
        



## Filter given data
def filterPools(token_symbol):
    with open('uni_v2_sushi_pools.csv', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=",", quotechar='"')
        data = [row for row in reader]
        
    filtered_pools = [data[0]]+ [pair for pair in data if token_symbol in pair]
        
    # Write CSV file
    with open("uni_v2_sushi_pools_filtered.csv", "wt") as fp:
        writer = csv.writer(fp, delimiter=",")
        writer.writerows(filtered_pools)

def getFilteredPools():
    with open('uni_v2_sushi_pools_filtered.csv', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=",", quotechar='"')
        data = [row for row in reader]
    return data
    

def loadTopPools(w3):
    with open('data/list_of_top_weth_pools.csv', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=",", quotechar='"')
        data = [w3.toChecksumAddress(row[0]) for row in reader]
    return data
    
def loadData(w3,pool_address):    
    f = open('data/raw/data_'+w3.toChecksumAddress(pool_address)+'_.json')
    data = json.load(f)
    return data
    
## Uniswap

def decodeSwapLogs(w3, pool_address, logs_swap):
    abi = '[{"inputs":[],"payable":false,"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"spender","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"sender","type":"address"},{"indexed":false,"internalType":"uint256","name":"amount0","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"amount1","type":"uint256"},{"indexed":true,"internalType":"address","name":"to","type":"address"}],"name":"Burn","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"sender","type":"address"},{"indexed":false,"internalType":"uint256","name":"amount0","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"amount1","type":"uint256"}],"name":"Mint","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"sender","type":"address"},{"indexed":false,"internalType":"uint256","name":"amount0In","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"amount1In","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"amount0Out","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"amount1Out","type":"uint256"},{"indexed":true,"internalType":"address","name":"to","type":"address"}],"name":"Swap","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"uint112","name":"reserve0","type":"uint112"},{"indexed":false,"internalType":"uint112","name":"reserve1","type":"uint112"}],"name":"Sync","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Transfer","type":"event"},{"constant":true,"inputs":[],"name":"DOMAIN_SEPARATOR","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"MINIMUM_LIQUIDITY","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"PERMIT_TYPEHASH","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"to","type":"address"}],"name":"burn","outputs":[{"internalType":"uint256","name":"amount0","type":"uint256"},{"internalType":"uint256","name":"amount1","type":"uint256"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"factory","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"getReserves","outputs":[{"internalType":"uint112","name":"_reserve0","type":"uint112"},{"internalType":"uint112","name":"_reserve1","type":"uint112"},{"internalType":"uint32","name":"_blockTimestampLast","type":"uint32"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"_token0","type":"address"},{"internalType":"address","name":"_token1","type":"address"}],"name":"initialize","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"kLast","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"to","type":"address"}],"name":"mint","outputs":[{"internalType":"uint256","name":"liquidity","type":"uint256"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"nonces","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"permit","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"price0CumulativeLast","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"price1CumulativeLast","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"to","type":"address"}],"name":"skim","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"uint256","name":"amount0Out","type":"uint256"},{"internalType":"uint256","name":"amount1Out","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"swap","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[],"name":"sync","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"token0","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"token1","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"}],"name":"transfer","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"}],"name":"transferFrom","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"}]'
    poolc = w3.eth.contract(address=pool_address, abi=abi)
    swaps = [poolc.events.Swap().processLog(log) for log in logs_swap]
    return swaps

def getFeesDecimal(swap,fee,decimals):
    total0swap = abs(swap['args']['amount0In'] - swap['args']['amount0Out'])
    total1swap = abs(swap['args']['amount1In'] - swap['args']['amount1Out'])
    return total0swap*fee*decimals, total1swap*fee*decimals

def getTotalFeesDecimal(swaps,fee,decimals):
    sum_T0, sum_T1 = 0, 0
    for swap in swaps:
        fee_0, fee_1= getFeesDecimal(swap,fee,decimals)
        sum_T0 += fee_0
        sum_T1 += fee_1
    return sum_T0, sum_T1

def getTotalFees(w3,  pool_address):
    fee = 0.3/100
    decimals = 10**-18
    print(pool_address)
    swap_hash = '0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822'
    logs = w3.eth.get_logs({'fromBlock': 'earliest',   'toBlock': 'latest',   'address': w3.toChecksumAddress(pool_address)  }) 
    logs_swap = [log for log in logs if log['topics'][0].hex()==swap_hash] 
    logs_swap = decodeSwapLogs(w3, pool_address, logs_swap)
    total_fees_0, total_fees_1 = getTotalFeesDecimal(logs_swap,fee,decimals)
    return total_fees_0, total_fees_1
 