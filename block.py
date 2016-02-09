filepath = '/home/pi/pybits/block_list.txt'

# get block hash from bitcoind command
from sys import argv
script, hash = argv

# json
import json

# current time
from datetime import datetime

# initialize bitcoin RPC connection and gather info
import bitcoinAuth
from bitcoinrpc import AuthServiceProxy, JSONRPCException
rpc_connection = AuthServiceProxy("http://%s:%s@127.0.0.1:8332"%(bitcoinAuth.USER,bitcoinAuth.PW))

#open file or create new
f = open(filepath,'a')
f.close()
f = open(filepath,'r+')

# read data from file
data = f.read()
if data:
	dataJson = json.loads(data)
else:
	dataJson = json.loads("{}")

# move file pointer back to top
f.seek(0)

# get info from this latest block we just learned about
blockInfo = rpc_connection.getblock(hash)
height = str(blockInfo['height'])
time = datetime.utcnow().strftime('%B %d %Y - %H:%M:%S')
block = {"hash":hash, "time":time}

# insert into JSON from file
dataJson[height] = block

# limit JSON file to n past blocks
while (len(dataJson) > 30):
	key = min(dataJson.keys())
	del dataJson[key]

# convert back to string and write to file
dataJsonString = json.dumps(dataJson)
f.write(dataJsonString)

# close file
f.close()

raise SystemExit("New Block: " + height)
