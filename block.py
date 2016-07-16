#!/usr/bin/env python

################
# dependencies #
################

import sys
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

rootdir = sys.path[0]
blockFile = rootdir + '/data/block_list.txt'
tmpFile =  rootdir + '/data/tmp' + str(int(os.urandom(4).encode('hex'), 16)) + '.txt'

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
	# get info from this latest block we just learned about
	blockInfo = rpc_connection.getblock(hash)
	height = str(blockInfo['height'])
	version = str(blockInfo['version'])
	size = str(blockInfo['size'])
	time = datetime.utcnow().strftime('%B %d %Y - %H:%M:%S')
	block = {"hash":hash, "height":height, "version":version, "size":size, "time":time}
	
	# create new file if missing
	if not os.path.isfile(blockFile):
		# create directory if missing
		if not os.path.exists(rootdir + '/data'):
			os.makedirs(rootdir + '/data')
			os.chmod(rootdir + '/data', 0777)

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
	# catch 'file not found' errors in race condition against another simultaneous thread
	try:
		os.rename(tmpFile, blockFile)
	except:
		import time
		import shutil
		errtmp = rootdir + '/data/4_tmpAboutToWrite_' + str(int(time.time())) + '.txt'
		errblock = rootdir + '/data/1_blockReadFirstFromDisk_' + str(int(time.time())) + '.txt'
		errExistBlock = rootdir + '/data/2_block_fileExistingAtWriteTime_' + str(int(time.time())) + '.txt'
		errdir = rootdir + '/data/3_ls_' + str(int(time.time())) + '.txt'
		
		errdirFile = open(errdir, 'w')
		errdirFile.write(str(list(os.walk(rootdir + '/data'))))
		errdirFile.close()
		
		errblockFile = open(errblock, 'w')
		errblockFile.write(data)
		errblockFile.close()
		
		errtmpFile = open(errtmp, 'w')
		errtmpFile.write(dataJsonString)
		errtmpFile.close()
		
		shutil.copyfile(blockFile, errExistBlock)
		
		raise




########
# MAIN #
########
#print
#print "--"
newBlock()
peers.refreshPeers()
