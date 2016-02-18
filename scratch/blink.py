
import random
import time
from rgbmatrix import Adafruit_RGBmatrix
matrix = Adafruit_RGBmatrix(32, 1)

x = 0

def zclear():
	for i in range(1000):
		matrix.SetPixel (random.randint(0,31), random.randint(0,31),0,0,0)
		time.sleep(.00125)
	

while True:
	pix = [ random.randint(0,31), random.randint(0,31), random.randint(0,255), random.randint(0,255), random.randint(0,255) ]
	matrix.SetPixel(pix[0],pix[1],pix[2],pix[3],pix[4])
	print x, pix
	x += 1
	if x == 500:
		x = 0
		zclear()
	time.sleep(.0025)
