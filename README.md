# The Bitcoin Block Clock

Raspberry Pi Full Node with 32 x 32 RGB LED network visualizer

## https://TheBitcoinBlockClock.com

### Dependencies:

* python-bitcoinrpc: https://github.com/jgarzik/python-bitcoinrpc (modified, included in this git as bitcoinrpc.py)

* Henner Zeller's RGB LED matrix driver: https://github.com/hzeller/rpi-rgb-led-matrix 

Be sure to install the Python bindings as well as the core library: https://github.com/hzeller/rpi-rgb-led-matrix/tree/master/bindings/python

You may also need to solder a jumper on the Adafruit HAT: https://github.com/hzeller/rpi-rgb-led-matrix#improving-flicker

* PyQRCode: https://pypi.python.org/pypi/PyQRCode:

```
$ sudo pip install pyqrcode
```

* PIL (now maintained as Pillow):
```
$ sudo apt-get install python-pil
```

* Bitcoin Core with the following lines added to `~/.bitcoin/bitcoin.config` (see Installation below, the paths should match):

```
blocknotify=python /home/pi/bin/ClockBlocker/block.py %s
walletnotify=python /home/pi/bin/ClockBlocker/tx.py %s
```

### Installation:

Clone this repository in ~/bin and make easy-to-type command to start clock:

```
$ cd ~
$ git clone https://github.com/pinheadmz/ClockBlocker.git
$ sudo ln -s ~/ClockBlocker/ledbits.py /usr/local/bin/ledbits
$ sudo chmod 777 /usr/local/bin/ledbits
```

...then from any command line you can start the clock by entering:

```
$ ledbits
```

### API passwords:

* Bitcoin: create file `bitcoinAuth.py` which contains:

```
USER = "YOUR-BITCOIN-RPC-USERNAME"
PW = "YOUR-BITCOIN-RPC-PASSWORD"
```

* IP geo-location service: Sign up for API key at http://www.ipinfodb.com/ip_location_api.php

...then create file `ipInfoAuth.py` which contains:

```
api_key = 'YOUR-API-KEY'
```

### Hardware & Parts:

All electronic components, acrylic enclosure and miscellaneous hardware needed
to build The Bitcoin Block Clock is listed
[on this spreadsheet](https://docs.google.com/spreadsheets/d/e/2PACX-1vQoqwZii8Q7Vff4G6VBbHY9nEBDpCbcJl7A2JQr04GaWl1P8F48w6u9bmrUHPezkEt8M4pJDIwM2e7H/pubhtml?gid=0&single=true). I always try to buy parts from adafruit.com or purse.io
so I can spend Bitcoin!

### Owner's manual

[Usage instructions](https://docs.google.com/document/d/e/2PACX-1vRi7wA3FIfBUQlZgS-69wufT3hh3Ql9BB_YaUYyeJwtmLlDsRau02cQcQiyQ-pIc6Z-0PLSzBtu4j9x/pub) are printed out and shipper to buyers with their order.
