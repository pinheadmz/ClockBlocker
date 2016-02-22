#!/usr/bin/env python

################
# dependencies #
################

import os
import peers
import json
import bitcoinAuth
from sys import argv
from datetime import datetime
from bitcoinrpc import AuthServiceProxy, JSONRPCException


#############
# constants #
#############

blockFile = '/home/pi/pybits/data/block_list.txt'

# amount of blocks to store in file
BLOCKMAX = 30


##############
# initialize #
##############

# from command line paramaters
script, hash = argv

# initialize bitcoin RPC connection and gather info
rpc_connection = AuthServiceProxy("http://%s:%s@127.0.0.1:8332"%(bitcoinAuth.USER,bitcoinAuth.PW))


#############
# functions #
#############

# get info about the new block, all we know is its hash from bitcoind
# -- TODO: if were creating the file check the block time in the blockchain
def newBlock():
	# create new file if missing
	if not os.path.isfile(blockFile):
		f = os.open(blockFile, os.O_CREAT)
		# script will be run both as root and user
		os.fchmod(f, 0777)
		os.close(f)
	
	# open file and read data
	f = open(blockFile,'r+')
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
	while (len(dataJson) > BLOCKMAX):
		key = min(dataJson.keys())
		del dataJson[key]

	# convert back to string and write to file
	dataJsonString = json.dumps(dataJson)
	f.write(dataJsonString)
	f.truncate()

	# close file
	f.close()

	#print "New Block: " + height


########
# MAIN #
########
#print
#print "--"
newBlock()
peers.refreshPeers()
