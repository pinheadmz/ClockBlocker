#!/usr/bin/sudo python

################
# dependencies #
################

try:
    import http.client as httplib
except ImportError:
    import httplib
import atexit
import curses
import pyqrcode
import time
import os
import json
import random
import socket
import bitcoinAuth
import sys
import random
from PIL import Image, ImageDraw, ImageFont
import peers
import copy
import hashlib

from datetime import datetime
from bitcoinrpc import AuthServiceProxy, JSONRPCException
from rgbmatrix import Adafruit_RGBmatrix


#############
# constants #
#############

# logs of bitcoin activity triggered by bitcoin.conf
rootdir = sys.path[0]
blockFile = rootdir + '/data/block_list.txt'
peerFile =  rootdir + '/data/peer_list.txt'
txFile =  rootdir + '/data/tx.txt'

# load font
font = ImageFont.load_path( rootdir + '/fonts/pilfonts/timR08.pil')

# brightness limits for random colors
DIM_MAX = 255
DIM_MED = 128
DIM_LOW = 100

# amount of time each LED row represents in seconds for block icons
TIMESCALE = 30

# maximum size of block in block history mode (in bytes)
MAX_BLOCKSIZE = 2000000

# block info number and thickness of block bars
BLOCK_BAR_HISTORY = 8
BLOCK_BAR_THICKNESS = 3

# default location of block hash on grid
HASH_X = 4
HASH_Y = 15

# size of block icons (squared)
ICONSIZE = 4

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
MEMPOOLSCALE = 1

# refresh rate in seconds
REFRESH = 1

# number of seconds to display QR code for tip, also balance and other texts
QRTIME = 5

# flag to "mute" LED grid
LEDGRID = True

# rotate grid output: 0, 90, 180, 270
ROTATE = 180

##############
# initialize #
##############

# runs on script exit, resets terminal settings
def cleanup():
	time.sleep(5)

	# undo curses settings
	curses.nocbreak()
	curses.echo()
	curses.endwin()
	
	matrix.Clear()
	print "bye!"
atexit.register(cleanup)

# make sure terminal setting is compatible with curses
# apparently this is really bad practice, bypass
#os.environ['TERM'] = 'xterm-256color'

# init curses for text output and getch()
stdscr = curses.initscr()
curses.start_color()
curses.noecho()
curses.halfdelay(REFRESH * 10) # reset with nocbreak, blocking value is x 0.1 seconds
# store window dimensions
MAXYX = stdscr.getmaxyx()
# some terminals don't like invisible cursors
try:
	curses.curs_set(0)
	invisCursor = True
except curses.error:
	invisCursor = False

# color pairs for curses, keeping all colors < 8 for dumb terminals
COLOR_GOLD = 1
curses.init_pair(COLOR_GOLD, 3, 0)
COLOR_LTBLUE = 7
curses.init_pair(COLOR_LTBLUE, 6, 0)
COLOR_GREEN = 2
curses.init_pair(COLOR_GREEN, 2, 0)
COLOR_WHITE = 3
curses.init_pair(COLOR_WHITE, 7, 0)
COLOR_RED = 6
curses.init_pair(COLOR_RED, 1, 0)
COLOR_PINK = 5
curses.init_pair(COLOR_PINK, 5, 0)
COLOR_BLUE = 4
curses.init_pair(COLOR_BLUE, 4, 0)

# init the bitcoin RPC connection
rpc_connection = AuthServiceProxy("http://%s:%s@127.0.0.1:8332"%(bitcoinAuth.USER,bitcoinAuth.PW))

# init LED grid, rows and chain length are both required parameters:
matrix = Adafruit_RGBmatrix(32, 1)

# this matrix buffers the LED grid output to avoid using clear() every frame
buffer = []

# this array stores hashes of blocks that confirms my incoming transactions
myTxBlocks = []
# on startup, load 10 (bitcoin RPC call default) recent receive transactions into that array
listTx = rpc_connection.listtransactions()
for tx in listTx:
	if tx['category'] == 'receive' and tx['confirmations'] > 0:
		myTxBlocks.append(tx['blockhash'])

# on startup, get my own user agent
myUserAgent = rpc_connection.getnetworkinfo()['subversion']

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
def bufferDraw(fadeIn=False):
	if fadeIn:
                for dots in range(1000):
                        (randX, randY) = (random.randint(0,31), random.randint(0,31))
			if ROTATE == 0:
                                matrix.SetPixel(randX, randY, *buffer[randX][randY])
                        elif ROTATE == 90:
                                matrix.SetPixel(randX, randY, *buffer[randY][31-randX])
                        elif ROTATE == 180:
                                matrix.SetPixel(randX, randY, *buffer[31-randX][31-randY])
                        elif ROTATE == 270:
                                matrix.SetPixel(randX, randY, *buffer[31-randY][randX])
			time.sleep(0.001)

	for x in range(32):
		for y in range(32):
			if ROTATE == 0:
				matrix.SetPixel(x, y, *buffer[x][y])
			elif ROTATE == 90:
				matrix.SetPixel(x, y, *buffer[y][31-x])
			elif ROTATE == 180:
				matrix.SetPixel(x, y, *buffer[31-x][31-y])
			elif ROTATE == 270:
				matrix.SetPixel(x, y, *buffer[31-y][x])
			


# stash cursor in the bottom right corner in case terminal won't invisiblize it
def hideCursor():
	stdscr.addstr(MAXYX[0]-1, MAXYX[1]-1, "")


# color certain text depending on type of node
def getUserAgentColor(subver):
	'''
	userAgent = subver.lower()
	if "classic" in userAgent:
		color = COLOR_GOLD
	elif "unlimited" in userAgent:
		color = COLOR_LTBLUE
	elif "xt" in userAgent:
		color = COLOR_GREEN
	elif "satoshi" not in userAgent:
		color = COLOR_RED
	else:
		color = COLOR_WHITE
	
	return color
	'''
	hash = hashlib.sha256(subver).hexdigest()
	return curses.color_pair((int(hash[10:20], 16) % 7) + 1)

# turn any arbitrary string into a (r, g, b) color via hash
def stringToColor(s):
	offset = 1
	hash = hashlib.sha256(s).hexdigest()
	color = (int(hash[offset:offset+2], 16), int(hash[offset+2:offset+4], 16), int(hash[offset+4:offset+6], 16))
	return color

# check for keyboard input -- also serves as the pause between REFRESH cycles
def checkKeyIn():
	keyNum = stdscr.getch()
	if keyNum == -1:
		return False
	else:
		key = chr(keyNum)

	if key in ("d", "D"):
		deposit()
	elif key in ("q", "Q"):
		sys.exit()
	elif key in ("b", "B"):
		showValue("balance")
	elif key in ("p", "P"):
		party(2)
	elif key in ("w", "W"):
		withdraw()
	elif key in ("h", "H"):
		showHistory()
	elif key in ("r", "R"):
		res = peers.refreshPeers()
		printMsg(res)
		time.sleep(2)
	elif key in ("l", "L"):
		global LEDGRID
		LEDGRID = not LEDGRID


# use curses to output a line (or two) of text towards bottom of the screen
def printMsg(msg, color=COLOR_WHITE, line=0):
	stdscr.erase()
	stdscr.addstr(2 + line, 0, msg, curses.color_pair(color))
	hideCursor()
	stdscr.refresh()


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
	draw.text((0, -2 + top), whole + ".", font=font, fill=(stringToColor(value) if not color else color))
	draw.text((5, 6 + top), dec[0:4], font=font, fill=(stringToColor(value) if not color else color))
	draw.text((13, 14 + top), dec[4:8], font=font, fill=(stringToColor(value) if not color else color))
	
	# align image, push to LED grid, and wait
	image=image.rotate(270-ROTATE)
	matrix.Clear()
	matrix.SetImage(image.im.id, 0, 0)
	time.sleep(QRTIME)


# fun random color glittery mayhem party!
def party(loops):
	# celebrate!
	for x in range(loops):
		# color splatter
		for y in range(400):
			pix = (random.randint(0,31), random.randint(0,31), random.randint(0,255), random.randint(0,255), random.randint(0,255))
			matrix.SetPixel(*pix)
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
		if tx['confirmations'] > 0:
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


# get an address to deposit money in
def deposit():
	printMsg("Loading bitcoin address...")

	# connect to node and get new wallet address
	try:
		addr = rpc_connection.getnewaddress()
	except (socket.error, httplib.CannotSendRequest):
		printMsg("getnewaddress http error", COLOR_RED)
		time.sleep(2)
		return False

	# show off the new address!
	printMsg(addr, COLOR_GREEN, 1)
	showQR(addr, 'M')


# called by withdraw() to display segment of a list as a menu
def withdrawMenu(coins, offset = 0):
	# display 10 coins at a time
	menuCoins = dict(coins.items()[0 + offset : 10 + offset])

	# display menu of coins to withdraw
	stdscr.erase()
	for i, key in enumerate(menuCoins):
		s = '%-3.4s%-13.13s%-40.40s' % (str(i) + ":", str(menuCoins[key]), key)
		stdscr.addstr(0 + i, 0, s)
	stdscr.addstr(0 + i + 2, 0, "Enter number of key to withdraw, [P]age next, or e[X]it")
	hideCursor()
	stdscr.refresh()
	
	# wait a bit longer this time
	curses.halfdelay(10 * 10)
	choice = stdscr.getch()
	if 48 <= choice <= 57:
		choiceChar = int(chr(choice))
	elif choice != -1:
		choiceChar = chr(choice)
	else:
		choiceChar = choice

	# then reset to original value
	curses.halfdelay(REFRESH * 10)

	# action based on user input
	if choiceChar in (-1, "x", "X"):
		return False
	elif choiceChar in ("p", "P"):
		offset = offset + 10 if offset + 10 < len(coins) else 0
		withdrawMenu(coins, offset)		
	elif isinstance(choiceChar, int) and int(choiceChar) <= len(menuCoins) - 1:
		chosenAddr = menuCoins.keys()[int(choiceChar)]
		# allow long string of input:
		curses.nocbreak()

		# get password (echo is still off!)	
		stdscr.addstr(0 + i + 3, 0, "Enter wallet password...")
		hideCursor()
		pwd = stdscr.getstr()
		
		# reset to original value
		curses.halfdelay(REFRESH * 10)
		
		# get that key from bitcoin
		try:
			checkPwd = rpc_connection.walletpassphrase(pwd, 60)
		except JSONRPCException:
			pass
		
		try:
			privKey = rpc_connection.dumpprivkey(chosenAddr)
		except JSONRPCException:
			printMsg("Wallet or passphrase error", COLOR_RED)
			time.sleep(2)
			return False
		
		try:
			rpc_connection.walletlock()
		except:
			pass

		# show off the new address!
		printMsg(privKey, COLOR_GREEN, 1)
		showQR(privKey, 'L')
	else:
		printMsg("Invalid selection", COLOR_RED)
		time.sleep(2)
		return False


# list addresses with unspent coins and reveal selected private key by QR code
def withdraw():
	printMsg("Loading unspent coins...")

	# connect to node and get all unspent outputs
	try:
		list = rpc_connection.listunspent(0)
	except (socket.error, httplib.CannotSendRequest):
		printMsg("listunspent http error", COLOR_RED)
		time.sleep(2)
		return False
		
	# no coins
	if len(list) == 0:
		printMsg("No unspent outputs!", COLOR_RED)
		time.sleep(2)
		return False

	# calculate balances of each spendable key in wallet
	coins = {}
	for addr in list:
		if addr['address'] in coins:
			coins[addr['address']] += addr['amount']
		else:
			coins[addr['address']] = addr['amount']
	
	# send unspent coins list to the recursive paging menu function
	withdrawMenu(coins)


# display bitcoin address QR code for tipping
def showQR(addr, errcorr):
	# generate QR code and display on LED grid
	code = pyqrcode.create(addr, error=errcorr, version=3)
	t = code.text(1)
	
	row = 31
	col = 0
	bufferInit()
	for i in t:
		if i != '\n':
			bufferPixel(row, col, 255-int(i)*255, 255-int(i)*255, 255-int(i)*255)
			col += 1
		else:
			row -= 1
			col = 0
			bufferDraw()
			#time.sleep(0.001)
	
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
	
	for x in range(drawDots + 1):
		if x == drawDots:
			# last dot will indicate fraction of the regular color
			bufferPixel(row, col, int(lastDot * 100), 255-int(lastDot*255), int(lastDot * 200))
		else:
			# regular "full" dot -- purple?
			bufferPixel(row, col, 100, 0, 200)

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
	
	for x in range(drawDots + 1):
		if x == drawDots:
			# last dot will indicate fraction of the regular color
			bufferPixel(row, col, 255 - int(lastDot * 255), int(lastDot * 200), int(lastDot * 100))
		else:
			# regular "full" dot -- aqua?
			bufferPixel(row, col, 0, 200, 100)

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
		# color changes each time we fill up the space
		layer = x/maxDots
		layerColors = [(0,255,0), (127, 127, 0), (255, 0, 0), (127, 0, 127), (0, 0, 255), (0, 127, 127)]
		color = layerColors[layer % len(layerColors)]
		bufferPixel(row, col, *color)
		
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


# show information about the last 8 blocks 
def showHistory():
	# total dots a full block fills up
	maxDots = BLOCK_BAR_THICKNESS * 32

	# number of bytes represented by each LED
	dotValue = MAX_BLOCKSIZE/maxDots

	# clear buffer
	bufferInit()
	
	# sort block info data by height
	heightHistory = sorted(fullBlockData)
	heightHistory.reverse()
	
	# draw block info bars to buffer and write to terminal screen
	stdscr.erase()
	m =  '%-7.6s%-9.9s%-12.10s%-66.64s' % ('Height', '  Size', '  Version', '  Hash')
	stdscr.addstr(1, 0, m, curses.A_UNDERLINE)
	for i in range(0, min(BLOCK_BAR_HISTORY, len(fullBlockData))):
		block = fullBlockData[heightHistory[i]]
		extraVersion = ""
		if "/EB" in block['coinbase'] and "/AD" in block['coinbase']:
			extraVersion += "EmergentConsensus"
		if "/NYA" in block['coinbase']:
			extraVersion += "NewYorkAgreement"
		if "/EXTBLK" in block['coinbase']:
			extraVersion += "ExtensionBlock"
		blockColor = stringToColor(block['version'] + extraVersion)
		
		# invert color for witness bytes
		blockColorINV = tuple(255-x for x in blockColor)
		
		blockSize = int(block['size'])
		strippedSize = int(block['strippedSize'])
		# calculate witness bytes but don't include coinbase witness (for now, early adoption phase)
		witnessBytes = blockSize - strippedSize - 36

		# calculate dots needed for base and witness
		drawWitnessDots = witnessBytes/dotValue
		drawWitnessDots = drawWitnessDots + 1 if witnessBytes > 0 else 0
		drawBaseDots = strippedSize/dotValue
		drawBaseDots = drawBaseDots + 1 if (witnessBytes%dotValue + strippedSize%dotValue + 36 >= dotValue) else drawBaseDots
		
		# start each bar with one col of space, right to left!
		COLMIN = 32 - ((i+1) * (BLOCK_BAR_THICKNESS + 1))
		COLMAX = COLMIN + BLOCK_BAR_THICKNESS - 1
		row = 31
		col = COLMIN

		# draw BASE block bytes, always light at least 1 LED
		for x in range(drawBaseDots):			
			if col < 0 or col > 31 or row < 0 or row > 31:
				break
			
			bufferPixel(row, col, *blockColor)
			
			if col < COLMAX:
				col += 1
			else:
				col = COLMIN
				row -= 1
			if row < 0:
				row = 32

		# draw WITNESS block bytes, only light if witness is present beyond coinbase
		for x in range(drawWitnessDots):
			if col < 0 or col > 31 or row < 0 or row > 31:
				break

			bufferPixel(row, col, *blockColorINV)

			if col < COLMAX:
				col += 1
			else:
				col = COLMIN
				row -= 1
			if row < 0:
				row = 32

		
		# print to screen
		s =  '%-7.6s%9.9s%12.10s%66.64s' % (heightHistory[i], '{:,}'.format(int(block['size'])), "0x%0*x" % (8, int(block['version'])), block['hash'])
		if "/EB" in block['coinbase'] and "/AD" in block['coinbase']:
			stdscr.addstr(2+(2*i), 0, s, curses.color_pair((int(block['version']) * 2 % 7)) + 1)
		else:
			stdscr.addstr(2+(2*i), 0, s, curses.color_pair((int(block['version']) % 7)) + 1)
		
		try:
			t =  '%-7.6s%9.9s%14.10s%-66.64s' % ("", "", "", block['coinbase'])
			stdscr.addstr(3+(2*i), 0, t, curses.color_pair(COLOR_WHITE))
		except KeyError:
			pass

	# terminal menu
	stdscr.addstr(MAXYX[0]-1, 0, "Press any key to return", curses.color_pair(COLOR_RED))
		
	# output
	bufferDraw()
	hideCursor()
	stdscr.refresh()
	#printMsg("Press any key to return", COLOR_RED)
	

	# wait for any key to exit
	while stdscr.getch() == -1:
		pass



#####################
### THE MAIN LOOP! ##
#####################

previousHeight = 0

while True:		
	# connect to node and get current mem pool size
	try:
		mempoolInfo = rpc_connection.getmempoolinfo()
	except (socket.error, httplib.CannotSendRequest):
		printMsg("getmempoolinfo http error", COLOR_RED)
		time.sleep(2)
		continue	
	numTx = mempoolInfo['size']
	memBytes = mempoolInfo['bytes']
	
	# load recent block info from file created by blocks.py
	if not os.path.isfile(blockFile):
		printMsg("No block history file, loading best block...", COLOR_RED)
		bestHash = rpc_connection.getbestblockhash()
		os.system("python " + rootdir + "/block.py " + str(bestHash))
	f = open(blockFile,'r')
	d = f.read()
	blockData = json.loads(d)	
	f.close()
	
	# load peers info from file
	if not os.path.isfile(peerFile):
		peers.refreshPeers()
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
	# backup before destructing
	fullBlockData = copy.deepcopy(blockData)
	
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
	
	# throw a party every block
	if previousHeight != latestHeight:
		party(2)
		fadeIn=True
	else:
		fadeIn=False
	previousHeight = latestHeight
	
	#############################
	# BEGIN DRAWING TO LED GRID #
	#############################
	#clear buffer
	bufferInit()

	if LEDGRID:
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
	bufferDraw(fadeIn)

	######################################
	# PRINT ADDITIONAL OUTPUT TO CONSOLE #
	######################################
	# console is 94x28
	stdscr.erase()
	
	stdscr.addstr(0, 0, "Block height: " + str(latestHeight))
	
	stdscr.addstr(1, 0, "Blocks until next difficulty adjustment: " + str(2016-int(latestHeight)%2016))
	
	stdscr.addstr(2, 0, "Blocks until next subsidy halvening: " + str(210000 - int(latestHeight)%210000))
	
	stdscr.addstr(3, 0, "Mempool TX's: " + str(numTx) + " -- Memory: " + str(memBytes) + " bytes")
	
	stdscr.addstr(5, 0, "Connected peers:", curses.A_UNDERLINE)
	line = 5
	for peer in peerData:
		line += 1
		# color each line depending on type of node
		color = getUserAgentColor(peer['subver'])
		
		# some subver's have sub-SUB-vers! eg Bitcoin Unlimited
		#subsubver = peer['subver'].split('(')
		#peer['subver'] = subsubver[0]

		s =  '%-23.22s%-38.37s%-18.17s%-16.15s' % (peer['addr'], peer['subver'], peer['country'], peer['city'])
		stdscr.addstr(line, 0, s, color)
		
		# add subsubver on new line if present
		#if len(subsubver) > 1:
		#	line += 1
		#	s = '%-25.24s%-27.26s' % ('', '(' + subsubver[1])
		#	stdscr.addstr(line, 0, s, curses.color_pair(color))


	menu = "[D]eposit  [W]ithdraw  [B]alance  [P]arty!  [Q]uit  [R]efresh peers  [H]istory  [L]ED Grid"
	stdscr.addstr(MAXYX[0]-1, 0, menu)
	
	# our own user agent goes up top
	uaLength = len(myUserAgent)
	stdscr.addstr(0, MAXYX[1] - uaLength, myUserAgent, getUserAgentColor(myUserAgent))
	
	# if cursor is visible get it out of the way
	hideCursor()

	# push text buffer to terminal display
	stdscr.refresh()
	
	# check for keyboard input and pause before display refresh
	checkKeyIn()
