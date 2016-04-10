# The Bitcoin Block Clock

Raspberry Pi Full Node with 32 x 32 RGB LED network visualizer
-
### Dependencies:

* python-bitcoinrpc: https://github.com/jgarzik/python-bitcoinrpc (modified, included in this git as bitcoinrpc.py)

* Adafruit RGB LED matrix driver: https://github.com/adafruit/rpi-rgb-led-matrix/ (modified, compiled and included in this git as rgbmatrix.so)

* PyQRCode: https://pypi.python.org/pypi/PyQRCode:
```
$ pip install pyqrcode
```

* Bitcoin Core (or alt-client, check out http://raspnode.com/diy.html) with the following lines added to `~/.bitcoin/bitcoin.config`:
```
blocknotify=python /PATH-TO-DIRECTORY/block.py %s
walletnotify=python /PATH-TO-DIRECTORY/tx.py %s
```

other helpful `bitcoin.config` parameters for running a full node on an RPi:
```
minrelaytxfee=0.00005000
limitfreerelay=0
dbcache=50
```
other tips for running a full node on an RPi:
* use an SSD drive (not a USB memory stick) for the blockchain
* Bitcoin Core version 0.12 employs `libsecp256k1` which improves block validation time a great deal


### Installation:

Clone this repository, then modify the "constants" lines in `block.py`, `peers.py`, `tx.py`, and `ledbits.py` so the file paths are correct:
```
#############
# constants #
#############

blockFile = '/PATH-TO-DIRECTORY/data/block_list.txt'
tmpFile = '/PATH-TO-DIRECTORY/data/tmp.txt'
peerFile = '/PATH-TO-DIRECTORY/data/peer_list.txt'
txFile = '/PATH-TO-DIRECTORY/data/tx.txt'
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
api_username = 'YOUR-USERNAME'
api_pw = 'YOUR-PASSWORD'
api_key = 'YOUR-API-KEY'
```

### Hardware:
Here's a "wishlist" I made on Adafruit (accepts Bitcoin!) with most the components I used for the build:

https://www.adafruit.com/wishlists/394607

A few of these items might be found cheaper on other sites, but this is overall the shopping list.
I didn't include HDMI or USB cables, or the materials I used in my own "custom" power distributor, but that Adafruit 10A power supply is enough to run the entire system.

Here's the SSD I'm using for the blockchain:

http://www.amazon.com/gp/product/B00EZ2FRU2