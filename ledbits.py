#!/usr/bin/env python

try:
    import http.client as httplib
except ImportError:
    import httplib

import pyqrcode
import time
import os
import json
import random
import socket
import bitcoinAuth
import sys, select, tty, termios

from datetime import datetime
from bitcoinrpc import AuthServiceProxy, JSONRPCException
from rgbmatrix import Adafruit_RGBmatrix

# log of blocks and times updated by block.py
filepath = '/home/pi/pybits/block_list.txt'

# capture current terminal settings before setting to one character at a time
old_settings = termios.tcgetattr(sys.stdin)

# brightness limits for random colors
DIM_MAX = 255
DIM_MED = 128
DIM_LOW = 100

# amount of time each LED row represents in seconds for block icons
TIMESCALE = 30

# default location of block hash on grid
HASH_X = 8
HASH_Y = 15

# size of block icons (squared)
ICONSIZE = 4

# mempool space
ROWMIN = 27
ROWMAX = 16
COLMIN = 8
COLMAX = 23

# number of mempool transactions each LED represents
MEMPOOLSCALE = 10

# refresh rate in seconds
REFRESH = 1

# number of seconds to display QR code for tip
QRTIME = 5

# init LED grid, rows and chain length are both required parameters:
matrix = Adafruit_RGBmatrix(32, 1)

#
# -- TODO buffer output to grid to eliminate flashing every clear
#

# init or hopefully reset the bitcoin RPC connection
rpc_connection = None
def initRPC():
	global rpc_connection
	rpc_connection = None
	rpc_connection = AuthServiceProxy("http://%s:%s@127.0.0.1:8332"%(bitcoinAuth.USER,bitcoinAuth.PW))
	print "New RPC connection:", rpc_connection

# check for keyboard input -- also serves as the pause between REFRESH cycles
def checkKeyIn():
	try:
		# one char at a time, no newline required
		tty.setcbreak(sys.stdin.fileno())

		sel = select.select([sys.stdin], [], [], REFRESH)
		
		if sel[0]:
			key = sys.stdin.read(1)
		else:
			key = False
	except KeyboardInterrupt:
		# reset terminal settings to normal expected behavior
		termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
		print "Interrupt caught waiting for keypress"
		sys.exit()
	finally:
		# reset terminal settings to normal expected behavior
		termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

	if key == "T" or key == "t":
		showQR()
		
		
# display bitcoin address QR code for tipping
def showQR():
	global rpc_connection
	print "Loading bitcoin address..."

	# connect to node and get new wallet address
	try:
		addr = rpc_connection.getnewaddress()
	except (socket.error, httplib.CannotSendRequest):
		print "showQR Timeout"
		initRPC()
		return False
	
	# bypass rpc for testing
	#addr = '1CepbXDXPeJTsk9PUUKkXwfqcyDgmo1qoE'
	
	
	# generate QR code and display on LED grid
	code = pyqrcode.create(addr, error='M', version=3)
	t = code.text(1)
	print addr
	
	# print the actual QR code to terminal with 1's and 0's
	#print t
	
	row = 31
	col = 0
	matrix.Clear()
	for i in t:
		if i != '\n':
			matrix.SetPixel(row, col, 255-int(i)*255, 255-int(i)*255, 255-int(i)*255)
			col += 1
		else:
			row -= 1
			col = 0
	
		time.sleep(0.001)
	
	# give us a chance to scan it
	time.sleep(QRTIME)
	return True

# draw the mempool
def drawMempool(txs):
	row = ROWMIN
	col = COLMIN
	maxDots = (ROWMIN - ROWMAX + 1) * (COLMAX - COLMIN + 1)

	# scale down mempool size for viewing	
	num = (txs/MEMPOOLSCALE)
	
	for x in range(num):
		# color changes each time we fill up the space and start over at the top
		# 'red' value may exceed 255 max if layer > 2
		layer = x/maxDots
		matrix.SetPixel(row, col, (layer)*127, 255/(layer+1), 0)
		
		if col < COLMAX:
			col += 1
		else:
			col = COLMIN
			row -= 1
		if row < ROWMAX:
			row = ROWMIN


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


#####################
### THE MAIN LOOP! ##
#####################
initRPC()
numTx = 0
memBytes = 0
while True:		
	# connect to node and get current mem pool size
	try:
		mempoolInfo = rpc_connection.getmempoolinfo()
		numTx = mempoolInfo['size']
		memBytes = mempoolInfo['bytes']
	except (socket.error, httplib.CannotSendRequest):
		print "mempoolInfo TIMEOUT ERROR!"
		initRPC()
		continue
	
	# load recent block info from file created by blocks.py
	f = open(filepath,'r')
	d = f.read()
	blockData = json.loads(d)
	f.close()
	
	# load info about as many recent blocks as can fit on grid given TIMESCALE and ICONSIZE
	now = datetime.utcnow()
	timeLimit = TIMESCALE * (33 - ICONSIZE) * 3
	recentBlocks = []
	elapsed = 0
	first = True
	while elapsed <= timeLimit and len(blockData) > 0:
		key = max(blockData.keys())
		block = blockData[key]
		blockTime = datetime.strptime(block['time'], '%B %d %Y - %H:%M:%S')
		elapsed = int((now - blockTime).total_seconds())
		blockInfo = {'time': elapsed, 'hash': block['hash'], 'index': key}
		if (elapsed <= timeLimit):
			recentBlocks.append(blockInfo)
		# save newest block in case nothing in range
		if first:
			first = False
			newestBlock = blockInfo
		del blockData[key]

	# use newest block if recent blocks are all out of range
	if len(recentBlocks) < 1:
		recentBlocks.append(newestBlock)
	
	latestHash = recentBlocks[0]['hash']
	latestHeight = recentBlocks[0]['index']

	#clear LED grid
	matrix.Clear()

	# draw latest block hash, bottom center
	drawHash(latestHash, HASH_X, HASH_Y)
	
	# draw block icons
	drawBlocks(recentBlocks, ICONSIZE)
	
	# draw mempool
	drawMempool(numTx)	

		
	# print additional stats to console
	os.system('clear')
	print "Block height:", latestHeight
	print
	print
	print "Blocks until next diff adj:", 2016-int(latestHeight)%2016
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
	print "Mempool TX's:", numTx, "memory:", memBytes/1000, "MB"	
	print
	print "Bytes:", "." * (memBytes/10000) + " " + str(memBytes)
	print
	print "Tx's:", "*" * (numTx/10) + " " + str(numTx)
	print

	# check for keyboard input
	checkKeyIn()

	# replaced by checkKeyIn()
	#time.sleep(REFRESH)
