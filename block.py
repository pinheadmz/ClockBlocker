#!/usr/bin/env python

################
# dependencies #
################

import sys
import os
import peers
import json
import bitcoinAuth
import time
from sys import argv
from datetime import datetime
from bitcoinrpc import AuthServiceProxy, JSONRPCException


#############
# constants #
#############

rootdir = sys.path[0]
blockFile = rootdir + '/data/block_list.txt'
tmpFile =  rootdir + '/data/tmp' + '_time-' + str(int(time.time())) + '_nonce-' + str(int(os.urandom(4).encode('hex'), 16)) + '.txt'

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
  strippedSize = str(blockInfo['strippedsize'])
  time = datetime.utcnow().strftime('%B %d %Y - %H:%M:%S')
  # get coinbase text -- REQUIRES txindex=1 in bitcoin.conf!
  txzero = blockInfo['tx'][0]
  txzeroinfo = rpc_connection.getrawtransaction(txzero, 1)
  coinbasehex = txzeroinfo['vin'][0]['coinbase']
  coinbasestring = ""
  for i in xrange(0, len(coinbasehex)-2, 2):
    c = coinbasehex[i:i+2]
    cint = int(c, 16)
    if not 126 > cint > 32:
      continue
    coinbasestring += chr(cint)      
  block = {"hash":hash, "height":height, "version":version, "size":size, "strippedSize":strippedSize, "time":time, "coinbase":coinbasestring}
  
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
  os.fchmod(tmp.fileno(), 0777)
  tmp.close()
  os.rename(tmpFile, blockFile)

########
# MAIN #
########
#print
#print("--")
newBlock()
peers.refreshPeers()
