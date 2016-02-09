import time
import bitcoinAuth
import pyqrcode
from bitcoinrpc import AuthServiceProxy, JSONRPCException
from rgbmatrix import Adafruit_RGBmatrix
matrix = Adafruit_RGBmatrix(32, 1)
matrix.Clear()

rpc_connection = AuthServiceProxy("http://%s:%s@127.0.0.1:8332"%(bitcoinAuth.USER,bitcoinAuth.PW))

addr = rpc_connection.getnewaddress()
code = pyqrcode.create(addr, error='M', version=3)
t = code.text(1)
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