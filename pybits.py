# to measure processing time and elapsed block time
from datetime import datetime
startTime = datetime.utcnow()

# for sleep
import time

# for reading JSON block info
import json

# initialize bitcoin RPC connection and gather mempool info
import bitcoinAuth
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
rpc_connection = AuthServiceProxy("http://%s:%s@127.0.0.1:8332"%(bitcoinAuth.USER,bitcoinAuth.PW))
mempoolInfo = rpc_connection.getmempoolinfo()
numTx = mempoolInfo['size']
mempoolSize = mempoolInfo['bytes']/float(1000000)

# load recent block info from file
f = open('block_list.txt','r')
d = f.read()
blockData = json.loads(d)
f.close()

# find the blocks that happened in past n hours
now = datetime.utcnow()
elapsed=120
latest = True
blockTimes =[]
TIMELIMIT = 60 * 60
while elapsed <= TIMELIMIT and len(blockData) > 0:
	key = max(blockData.keys())
	block = blockData[key]
	if latest:	
		latest = False
		latestHash = block['hash']
		latestHeight = key
	blockTime = datetime.strptime(block['time'], '%B %d %Y - %H:%M:%S')
	elapsed = int((now - blockTime).total_seconds())
	if (elapsed <= TIMELIMIT):
		blockTimes.append(elapsed/60)
	del blockData[key]

print
print "Recent block times in minutes ago:", blockTimes
print
print "Best block hash: ", latestHash
print
print "Best block height: ", latestHeight
print
print "Blocks since last diff adj:", int(latestHeight)%2016, "blocks ago at block:", int(latestHeight) - (int(latestHeight)%2016)
print
print "Mempool TX's:", numTx, "memory:", mempoolSize, "MB"
print

# cut block hash into 16x16 bits - 16 bits is 4 hex characters
for i in range(0,16):
	index = i*4
	chunk = latestHash[index:index+4]
	chunkBinary = bin(int(chunk, 16))[2:].zfill(16)
	print chunkBinary

# print total processing time
print "Running time: ",  datetime.utcnow() - startTime


