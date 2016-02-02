#!/usr/bin/env python

import time
import os
import json
import random
import bitcoinAuth

from datetime import datetime
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from rgbmatrix import Adafruit_RGBmatrix


# brightness limits for random colors
DIM_MAX = 255
DIM_MED = 128
DIM_LOW = 100

# amount of time each LED row represents in seconds for block icons
TIMESCALE = 60

# default location of block hash on grid
HASH_X = 8
HASH_Y = 15

# size of block icons (squared)
ICONSIZE = 4

# refresh rate in seconds
REFRESH = 1


# init LED grid, rows and chain length are both required parameters:
matrix = Adafruit_RGBmatrix(32, 1)

# init bitcoin RPC connection
rpc_connection = AuthServiceProxy("http://%s:%s@127.0.0.1:8332"%(bitcoinAuth.USER,bitcoinAuth.PW))


# draws a block hash on the grid from point (x, y)
def drawHash(hash, x, y):
	# keep the whole thing on the grid
	if x < 0 or x > 16 or y < 15 or y > 31:
		return False

	# choose colors from block hash least sig bits
	r1 = int(hash[-2:], 16) % DIM_MED + 100
	g1 = int(hash[-4:-2], 16) % DIM_MED + 100
	b1 = int(hash[-6:-4], 16) % DIM_MED + 100
	r0 = int(hash[-8:-6], 16) % DIM_MED
	g0 = int(hash[-10:-8], 16) % DIM_MED
	b0 = int(hash[-12:-10], 16) % DIM_MED

	# iterate through hash string and set pixels
	for row in range(0,16):  
        	index = row * 4
        	chunk = hash[index:index+4]
        	chunkBinary = bin(int(chunk, 16))[2:].zfill(16)
		for col, bit in enumerate(chunkBinary):		
			if bit == "1":
				matrix.SetPixel(y - row, x + col, r1, g1, b1)
			else:
				matrix.SetPixel(y - row, x + col, r0, g0, b0)

	return True


# draw block icons around outside perimeter of LED grid
def drawBlocks(recentBlocks, size):
	# size of icons must be at least 1x1 pixels
	size = size if size > 1 else 1
	
	for num, block in enumerate(recentBlocks):
		hash = block['hash']
		time = block['time']
		
		# choose color from block hash least sig bits
		r = int(hash[-2:], 16)
		g = int(hash[-4:-2], 16)
		b = int(hash[-6:-4], 16)
		
		# figure out where this block goes around the edge of grid
		t = time / TIMESCALE
		section = t / (33 - size)
		inc = t % (33 - size)

		# draw icon
		if section == 0:
			for x in range(size):
				for y in range(size):
					matrix.SetPixel(inc + x, 0 + y, r, g, b)
		elif section == 1:
			for x in range(size):
				for y in range(size):
					matrix.SetPixel(31 - x, inc + y, r, g, b)
		elif section == 2:
			for x in range(size):
				for y in range(size):
					matrix.SetPixel(31 - inc - x, 31 - y, r, g, b)


while True:	
	# connect to node and get current mem pool size
	mempoolInfo = rpc_connection.getmempoolinfo()
	numTx = mempoolInfo['size']
	mempoolSize = mempoolInfo['bytes']
	
	# load recent block info from file created by blocks.py
	f = open('block_list.txt','r')
	d = f.read()
	blockData = json.loads(d)
	f.close()
	
	# load info about as many recent blocks as can fit on grid given TIMESCALE and ICONSIZE
	now = datetime.utcnow()
	timeLimit = TIMESCALE * (33 - ICONSIZE) * 3
	recentBlocks = []
	elapsed = 0
	while elapsed <= timeLimit and len(blockData) > 0:
		key = max(blockData.keys())
		block = blockData[key]
		blockTime = datetime.strptime(block['time'], '%B %d %Y - %H:%M:%S')
		elapsed = int((now - blockTime).total_seconds())
		if (elapsed <= timeLimit):
			recentBlocks.append({'time': elapsed, 'hash': block['hash'], 'index': key})
		del blockData[key]
	latestHash = recentBlocks[0]['hash']
	latestHeight = recentBlocks[0]['index']

	#clear LED grid
	matrix.Clear()

	# draw latest block hash, bottom center
	drawHash(latestHash, HASH_X, HASH_Y)
	
	# draw block icons
	drawBlocks(recentBlocks, ICONSIZE)
	
	# print additional stats to console
	os.system('clear')
	print "Blocks until next diff adj:", 2016-int(latestHeight)%2016
	print "Last adj at block:", int(latestHeight) - (int(latestHeight)%2016)
	print
	pctSince =  int((int(latestHeight)%2016 / float(2016)) * 100)
	pctUntil = 100 - pctSince
	print "[" + ("+" * pctSince) + ("-" * pctUntil) + "]"
	print
	print "Blocks until next subsidy halvening:", 210000 - int(latestHeight)%210000
	print
	pctSinceB = int(int(latestHeight)%210000 / float(210000) * 100)
	pctUntilB = 100 - pctSinceB
	print "[" + ("+" * pctSinceB) + ("-" * pctUntilB) + "]"
	print
	print "Mempool TX's:", numTx, "memory:", mempoolSize, "MB"	
	print
	print "Bytes:", "." * (mempoolInfo['bytes']/10000) + " " + str(mempoolInfo['bytes'])
	print
	print "Tx's:", "*" * (numTx/10) + " " + str(numTx)
	print

	time.sleep(REFRESH)
