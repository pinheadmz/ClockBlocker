import time
import pyqrcode
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from rgbmatrix import Adafruit_RGBmatrix
matrix = Adafruit_RGBmatrix(32, 1)
matrix.Clear()
code = pyqrcode.create('1FSFNH32H3cZAjuGwtyJxrfYPQsYehfEkA', error='M', version=3)
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
	
while True:
	time.sleep(1)