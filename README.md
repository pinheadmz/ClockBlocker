# The Bitcoin Block Clock

Raspberry Pi Full Node with 32 x 32 RGB LED network visualizer
-
### Dependencies:

python-bitcoinrpc: https://github.com/jgarzik/python-bitcoinrpc (modified, included in this git as bitcoinrpc.py)

Adafruit RGB LED matrix driver: https://github.com/adafruit/rpi-rgb-led-matrix/ (modified, compiled and included in this git as rgbmatrix.so)

Bitcoin Core (or alt-client) with the following lines added to `~/.bitcoin/bitcoin.config`:
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

Modify the "constants" lines in `block.py`, `tx.py`, and `ledbits.py` so the file paths are correct:
```
#############
# constants #
#############

blockFile = '/PATH-TO-DIRECTORY/block_list.txt'
peerFile = '/PATH-TO-DIRECTORY/peer_list.txt'
txFile = '/PATH-TO-DIRECTORY/tx.txt'
```


### API passwords:

create file `bitcounAuth.py` which contains:
```
USER = "YOUR-BITCOIN-RPC-USERNAME"
PW = "YOUR-BITCOIN-RPC-PASSWORD"
```
Sign up for API key at http://www.ipinfodb.com/ip_location_api.php

...then create file `ipInfoAuth.py` which contains:
```
api_username = 'YOUR-USERNAME'
api_pw = 'YOUR-PASSWORD'
api_key = 'YOUR-API-KEY'
```