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
tmpFile = '/home/pi/pybits/data/tmp.txt'

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
	
	# open file, read data, then close
	f = open(blockFile,'r')
	data = f.read()
	f.close()
	
	if data:
		dataJson = json.loads(data)
	else:
		dataJson = json.loads("{}")

	# get info from this latest block we just learned about
	blockInfo = rpc_connection.getblock(hash)
	height = str(blockInfo['height'])
	version = str(blockInfo['version'])
	size = str(blockInfo['size'])
	time = datetime.utcnow().strftime('%B %d %Y - %H:%M:%S')
	block = {"hash":hash, "height":height, "version":version, "size":size, "time":time}

	# insert into JSON from file
	dataJson[height] = block

	# limit JSON file to n past blocks
	while (len(dataJson) > BLOCKMAX):
		key = min(dataJson.keys())
		del dataJson[key]

	# convert back to string and write to TEMP file for atomicity 
	dataJsonString = json.dumps(dataJson)
	tmp = open(tmpFile,'w')
	tmp.write(dataJsonString)
	
	# swap in new file and close
	tmp.flush()
	os.fsync(tmp.fileno())
	tmp.close()
	os.rename(tmpFile, blockFile)
	
	

########
# MAIN #
########
#print
#print "--"
newBlock()
peers.refreshPeers()
