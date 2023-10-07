#!/usr/bin/env python

################
# dependencies #
################

import sys
import os
import numbers
import decimal
import json
import bitcoinAuth
from sys import argv
from bitcoinrpc import AuthServiceProxy, JSONRPCException


#############
# constants #
#############

rootdir = sys.path[0]
txFile =  rootdir + '/data/tx.txt'

##############
# initialize #
##############

# from command line paramaters
script, txid = argv

# initialize bitcoin RPC connection and gather info
rpc_connection = AuthServiceProxy("http://%s:%s@127.0.0.1:8332"%(bitcoinAuth.USER,bitcoinAuth.PW))


#############
# functions #
#############

# because JSON dump hates decimals for soem reason
def allToString(obj):
	return str(obj)


########
# main #
########

# create new file if missing
if not os.path.isfile(txFile):
	# create directory if missing
	if not os.path.exists(rootdir + '/data'):
		os.makedirs(rootdir + '/data')
		os.chmod(rootdir + '/data', 0777)

	f = os.open(txFile, os.O_CREAT)
	# script will be run both as root and user
	os.fchmod(f, 0777)
	os.close(f)

# open file and read data
f = open(txFile,'r+')
data = f.read()
if data:
	dataJson = json.loads(data)
else:
	dataJson = json.loads("[]")

# move file pointer back to top
f.seek(0)

# get info from this latest tx we just learned about
txInfo = rpc_connection.gettransaction(txid)

# insert into JSON from file
dataJson.append(txInfo)

# convert back to string and write to file
dataJson = json.dumps(dataJson, default=allToString)

f.write(dataJson)
f.truncate()

# close file
f.close()

#print
#print("--")
#print("New Tx!")
