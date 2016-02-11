import time
import bitcoinAuth
import pyqrcode
import socket, httplib
from bitcoinrpc import AuthServiceProxy, JSONRPCException
from rgbmatrix import Adafruit_RGBmatrix
matrix = Adafruit_RGBmatrix(32, 1)
matrix.Clear()

rpc_connection = AuthServiceProxy("http://%s:%s@127.0.0.1:8332"%(bitcoinAuth.USER,bitcoinAuth.PW))

print "Loading 1st bitcoin address..."

addr = rpc_connection.getnewaddress()
code = pyqrcode.create(addr, error='M', version=3)
t = code.text(1)

print addr

print t

row = 31
col = 0

for i in t:
	if i != '\n':
		matrix.SetPixel(row, col, 255-int(i)*255, 255-int(i)*255, 255-int(i)*255)
		col += 1
	else:
		row -= 1
		col = 0
	
	time.sleep(0.001)

time.sleep(3)



def showQR():
	global rpc_connection
	print "Loading 2nd bitcoin address..."

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
	print t
	
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
	time.sleep(5)
	return True

print "starting"
showQR()
matrix.clear()
print "done"


