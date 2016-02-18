
import time
import Image
import ImageDraw
import ImageFont
import os
from rgbmatrix import Adafruit_RGBmatrix

font = ImageFont.load_path("/home/pi/pybits/fonts/pilfonts/timR08.pil")
#fontYoffset = -2  # Scoot up a couple lines so descenders aren't cropped

matrix = Adafruit_RGBmatrix(32, 1) # rows, chain length

image = Image.new('RGB', (32, 32))
draw = ImageDraw.Draw(image)

draw.text((0,-2), "0.", font=font, fill=(255,100,100))
draw.text((5,6), "1234", font=font, fill=(100,200,255))
draw.text((13,14), "5678", font=font, fill=(200,200,55))

image=image.rotate(270)
matrix.SetImage(image.im.id, 0, 0)

time.sleep(30)