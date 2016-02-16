#!/usr/bin/env python

################
# dependencies #
################

try:
    import http.client as httplib
except ImportError:
    import httplib
import atexit
import pyqrcode
import time
import os
import json
import random
import socket
import bitcoinAuth
import sys
import select
import tty
import termios
import random
import Image
import ImageDraw
import ImageFont

from datetime import datetime
from bitcoinrpc import AuthServiceProxy, JSONRPCException
from rgbmatrix import Adafruit_RGBmatrix


#############
# constants #
#############

# log of blocks and times updated by block.py
blockFile = '/home/pi/pybits/data/block_list.txt'
peerFile = '/home/pi/pybits/data/peer_list.txt'
txFile = '/home/pi/pybits/data/tx.txt'

# brightness limits for random colors
DIM_MAX = 255
DIM_MED = 128
DIM_LOW = 100

# amount of time each LED row represents in seconds for block icons
TIMESCALE = 30

# default location of block hash on grid
HASH_X = 4
HASH_Y = 15

# size of block icons (squared)
ICONSIZE = 3

# mempool space
MEM_ROWMIN = 27
MEM_ROWMAX = 17
MEM_COLMIN = 4
MEM_COLMAX = 27

# difficulty space
DIF_ROWMIN = 15
DIF_ROWMAX = 0
DIF_COLMIN = 21
DIF_COLMAX = 23

# subsidy space
SUB_ROWMIN = 15
SUB_ROWMAX = 0
SUB_COLMIN = 25
SUB_COLMAX = 27

# number of mempool transactions each LED represents
MEMPOOLSCALE = 5

# refresh rate in seconds
REFRESH = 1

# number of seconds to display QR code for tip, also balance and other texts
QRTIME = 5


##############
# initialize #
##############

# capture current terminal settings before setting to one character at a time
old_settings = termios.tcgetattr(sys.stdin)
def cleanup():
	# reset terminal settings to normal expected behavior
	termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
	# clear LED grid
	matrix.Clear()
	print "bye!"
atexit.register(cleanup)
# one char at a time, no newline required
tty.setcbreak(sys.stdin.fileno())

# init the bitcoin RPC connection
rpc_connection = AuthServiceProxy("http://%s:%s@127.0.0.1:8332"%(bitcoinAuth.USER,bitcoinAuth.PW))

# init LED grid, rows and chain length are both required parameters:
matrix = Adafruit_RGBmatrix(32, 1)

# load font
font = ImageFont.load_path("/home/pi/pybits/fonts/pilfonts/timR08.pil")

# this matrix buffers the LED grid output to avoid using clear() every frame
buffer = []

# this array stores hashes of blocks that confirms my incoming transactions
myTxBlocks = []

# TODO -- listtransactions in case we got confirmed before starting up (before newTx)



#############
# functions #
#############

# fill buffer matrix with black (off) pixels
def bufferInit():
	global buffer
	buffer = [[(0,0,0) for i in range(32)] for j in range(32)]

# change a pixel in the buffer
def bufferPixel(x, y, r, g, b):
	global buffer
	buffer[x][y] = (r, g, b)
	
# draw entire buffer to LED grid without needing clear()
def bufferDraw():
	for x in range(32):
		for y in range(32):
			matrix.SetPixel(x, y, buffer[x][y][0], buffer[x][y][1], buffer[x][y][2])


# check for keyboard input -- also serves as the pause between REFRESH cycles
def checkKeyIn():
	try:
		sel = select.select([sys.stdin], [], [], REFRESH)
		if sel[0]:
			key = sys.stdin.read(1)
		else:
			key = False
	except KeyboardInterrupt:
		print "Interrupt caught waiting for keypress"
		sys.exit()

	if key == "D" or key == "d":
		showQR()
	elif key == "Q" or key == "q":
		sys.exit()
	elif key == "B" or key == "b":
		showValue("balance")


# show wallet balance on screen
def showValue(value):
	#get the balance, default
	if value == "balance":
		wallet = rpc_connection.getwalletinfo()
		# add in unconfirmed balance for grand total -- so, not 0-conf safe I guess
		value = str(wallet['balance'] + wallet['unconfirmed_balance'])
		color = (50, 255, 50)
		top = 9
	else:
		color = False
		top = 0
	
	# edge case if you send yourself money -- TODO, better handling? I dunno
	value = value if value != "0E-8" else "0.00000000"
	
	# init image palette 
	image = Image.new('RGB', (32, 32))
	draw = ImageDraw.Draw(image)

	# break up digits and print text
	(whole, dec) = value.split(".")
	draw.text((0, -2 + top), whole + ".", font=font, fill=((255,100,100) if not color else color))
	draw.text((5, 6 + top), dec[0:4], font=font, fill=((100,200,255) if not color else color))
	draw.text((13, 14 + top), dec[4:8], font=font, fill=((200,200,55) if not color else color))
	
	# align image, push to LED grid, and wait
	image=image.rotate(270)
	matrix.Clear()
	matrix.SetImage(image.im.id, 0, 0)
	time.sleep(QRTIME)


# fun random color glittery mayhem party!
def party(loops):
	# celebrate!
	for x in range(loops):
		# color splatter
		for y in range(400):
			pix = [ random.randint(0,31), random.randint(0,31), random.randint(0,255), random.randint(0,255), random.randint(0,255) ]
			matrix.SetPixel(pix[0],pix[1],pix[2],pix[3],pix[4])
			time.sleep(.001)
		# clear a few holes
		for i in range(1000):
			matrix.SetPixel (random.randint(0,31), random.randint(0,31),0,0,0)
			time.sleep(.0005)
			
			
# received new incoming transaction
def newTx(txData):
	global myTxBlocks

	# don't need to show balance if just a confirmation message
	showBalance = False	
	for tx in txData:
		# only celebrate tx receive, but add confirmations to myTxBlocks
		if tx['confirmations'] == 1:
			myTxBlocks.append( tx['blockhash'] )
			continue
		
		# celebrate!
		party(4)
		showBalance = True

		# now show our received amount
		showValue( str(tx['amount']) )
	
	# done with all transactions, show final total balance
	if showBalance:
		party(1)
		showValue("balance")
		party(1)


# display bitcoin address QR code for tipping
def showQR():
	global rpc_connection
	print
	print "Loading bitcoin address..."

	# connect to node and get new wallet address
	try:
		addr = rpc_connection.getnewaddress()
	except (socket.error, httplib.CannotSendRequest):
		print "getnewaddress http error"
		return False
	
	# bypass rpc for testing
	#addr = '1CepbXDXPeJTsk9PUUKkXwfqcyDgmo1qoE'
	
	# generate QR code and display on LED grid
	print addr
	code = pyqrcode.create(addr, error='M', version=3)
	t = code.text(1)
	
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


# draw blocks since last difficulty adjustment
def drawDiff(height):
	since = int(latestHeight)%2016
	row = DIF_ROWMIN
	col = DIF_COLMIN
	maxDots = (DIF_ROWMIN - DIF_ROWMAX + 1) * (DIF_COLMAX - DIF_COLMIN + 1)

	# number of blocks represented by each LED
	dotValue = 2016/maxDots

	# therefore number of dots to draw are...
	drawDots = since/dotValue
	
	# last dot is a fraction
	lastDot = float(since%dotValue) / dotValue
	
	for x in range(drawDots):
		if (x+1) == drawDots:
			# last dot will indicate fraction from blue (emptiest) to red (fullest)
			bufferPixel(row, col, int(lastDot * 255), 0, 255 - int(lastDot * 255))
		else:
			# regular "full" dot -- purple?
			bufferPixel(row, col, 100, 0, 200)
		'''
		if row > DIF_ROWMAX:
			row -= 1
		else:
			row = DIF_ROWMIN
			col += 1
		# this shouldn't ever happen...
		if col > DIF_COLMAX:
			col = DIF_COLMIN
		'''
		if col < DIF_COLMAX:
			col += 1
		else:
			col = DIF_COLMIN
			row -= 1
		if row < DIF_ROWMAX:
			row = DIF_ROWMIN


# draw blocks since last subsidy halving
def drawSubsidy(height):
	since = int(latestHeight)%210000
	row = SUB_ROWMIN
	col = SUB_COLMIN
	maxDots = (SUB_ROWMIN - SUB_ROWMAX + 1) * (SUB_COLMAX - SUB_COLMIN + 1)

	# number of blocks represented by each LED
	dotValue = 210000/maxDots

	# therefore number of dots to draw are...
	drawDots = since/dotValue
	
	# last dot is a fraction
	lastDot = float(since%dotValue) / dotValue
	
	for x in range(drawDots):
		if (x+1) == drawDots:
			# last dot will indicate fraction from green (emptiest) to blue (fullest)
			bufferPixel(row, col, 0, 255 - int(lastDot * 255), int(lastDot * 255))
		else:
			# regular "full" dot -- purple?
			bufferPixel(row, col, 0, 200, 100)
		'''
		if row > SUB_ROWMAX:
			row -= 1
		else:
			row = SUB_ROWMIN
			col += 1
		# this shouldn't ever happen...
		if col > SUB_COLMAX:
			col = SUB_COLMIN
		'''
		if col < SUB_COLMAX:
			col += 1
		else:
			col = SUB_COLMIN
			row -= 1
		if row < SUB_ROWMAX:
			row = SUB_ROWMIN


# draw the mempool
def drawMempool(txs):
	row = MEM_ROWMIN
	col = MEM_COLMIN
	maxDots = (MEM_ROWMIN - MEM_ROWMAX + 1) * (MEM_COLMAX - MEM_COLMIN + 1)

	# scale down mempool size for viewing	
	num = txs/MEMPOOLSCALE
	
	for x in range(num):
		# color changes each time we fill up the space and start over at the top
		# 'red' value may exceed 255 max if layer > 2
		layer = x/maxDots
		bufferPixel(row, col, (layer)*127, 255/(layer+1), 0)
		
		if col < MEM_COLMAX:
			col += 1
		else:
			col = MEM_COLMIN
			row -= 1
		if row < MEM_ROWMAX:
			row = MEM_ROWMIN


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
				bufferPixel(y - row, x + col, r1, g1, b1)
			else:
				bufferPixel(y - row, x + col, r0, g0, b0)


# draw block icons around outside perimeter of LED grid
def drawBlocks(recentBlocks, size):
	# size of icons must be at least 1x1 pixels
	size = size if size > 1 else 1
	
	for num, block in enumerate(recentBlocks):
		hash = block['hash']
		time = block['time']
		if hash in myTxBlocks:
			myTx = True
		else:
			myTx = False
		
		# choose color from block hash least sig bits and boost overall brightness
		r = (int(hash[-2:], 16)%200) + 55
		g = (int(hash[-4:-2], 16)%200) + 55
		b = (int(hash[-6:-4], 16)%200) + 55
		
		# figure out where this block goes around the edge of grid
		t = time / TIMESCALE
		section = t / (33 - size)
		inc = t % (33 - size)

		# draw icon, default empty square, filled in for confirmed Tx
		if section == 0:
			for x in range(size):
				for y in range(size):
					if myTx:
						bufferPixel(inc + x, 0 + y, r, g, b)
					elif x == 0 or y == 0 or x == (size-1) or y == (size-1):
						bufferPixel(inc + x, 0 + y, r, g, b)
		elif section == 1:
			for x in range(size):
				for y in range(size):
					if myTx:
						bufferPixel(31 - x, inc + y, r, g, b)
					elif x == 0 or y == 0 or x == (size-1) or y == (size-1):
						bufferPixel(31 - x, inc + y, r, g, b)
		elif section == 2:
			for x in range(size):
				for y in range(size):
					if myTx:
						bufferPixel(31 - inc - x, 31 - y, r, g, b)
					elif x == 0 or y == 0 or x == (size-1) or y == (size-1):
						bufferPixel(31 - inc - x, 31 - y, r, g, b)


#####################
### THE MAIN LOOP! ##
#####################

while True:		
	# connect to node and get current mem pool size
	try:
		mempoolInfo = rpc_connection.getmempoolinfo()
	except (socket.error, httplib.CannotSendRequest):
		print "getmempoolinfo http error"
		continue	
	numTx = mempoolInfo['size']
	memBytes = mempoolInfo['bytes']
	
	# load recent block info from file created by blocks.py
	f = open(blockFile,'r')
	d = f.read()
	blockData = json.loads(d)
	f.close()
	
	# load peers info from file created by blocks.py
	p = open(peerFile,'r')
	pd = p.read()
	peerData = json.loads(pd)
	p.close()
	
	# check for a new Tx file, load, then delete it
	if os.path.isfile(txFile):
		t = open(txFile,'r')
		td = t.read()
		t.close()
		os.remove(txFile)
		if td:
			txData = json.loads(td)
			if txData:
				newTx(txData)
	
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
	
	#############################
	# BEGIN DRAWING TO LED GRID #
	#############################
	#clear buffer
	bufferInit()

	# draw latest block hash, bottom center
	drawHash(latestHash, HASH_X, HASH_Y)
	
	# draw block icons
	drawBlocks(recentBlocks, ICONSIZE)
	
	# draw mempool
	drawMempool(numTx)
	
	# draw difficulty period
	drawDiff(latestHeight)
	
	# draw subsidy period
	drawSubsidy(latestHeight)
	
	# push buffer to actual LED grid
	bufferDraw()

	######################################
	# PRINT ADDITIONAL OUTPUT TO CONSOLE #
	######################################
	os.system('clear')
	print "Block height:", latestHeight
	print
	print "Blocks until next difficulty adjustment:", 2016-int(latestHeight)%2016
	print
	print "Blocks until next subsidy halvening:", 210000 - int(latestHeight)%210000
	print
	print "Mempool TX's:", numTx, " -- Memory:", memBytes, "bytes"	
	print
	print "Connected peers:"
	for peer in peerData:
		print '%-25.24s%-27.26s%-20.19s%-20.19s' % (peer['addr'], peer['subver'], peer['country'], peer['city'])

	# check for keyboard input and pause before display refresh
	checkKeyIn()
