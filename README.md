# The Bitcoin Block Clock


Raspberry Pi Full Node with 32 x 32 RGB LED network visualizer
-
### Dependencies:

python-bitcoinrpc: https://github.com/jgarzik/python-bitcoinrpc (modified, included in this git as bitcoinrpc.py)

Adafruit RGB LED matrix driver: https://github.com/adafruit/rpi-rgb-led-matrix/ (modified, compiled and included in this git as rgbmatrix.so)

Bitcoin Core (or alt-client) with the following lines added to `~/.bitcoin/bitcoin.config`:
```
blocknotify=python /home/pi/pybits/block.py %s
walletnotify=python /home/pi/pybits/tx.py %s
```

other helpful `bitcoin.config` parameters for running a full node a RPi:
```
minrelaytxfee=0.00005000
limitfreerelay=0
dbcache=50
```
other tips for running a full node on a RPi:
* use a small SSD drive (not a USB memory stick) for the blockchain
* Bitcoin Core version 0.12 employs `libsecp256k1` which improves block validation time a great deal

### API passwords:

create file `bitcounAuth.py` which contains:
```
USER = "YOUR-BITCOIN-RPC-USERNAME"
PW = "YOUR-BITCOIN-RPC-PASSWORD"
```
Sign up for API key at http://www.ipinfodb.com/ip_location_api.php

create file `ipInfoAuth.py` which contains:
```
api_username = 'YOUR-USERNAME';
api_pw = 'YOUR-PASSWORD';
api_key = 'YOUR-API-KEY';
```

