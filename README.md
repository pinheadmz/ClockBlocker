Requires python-bitcoinrpc https://github.com/jgarzik/python-bitcoinrpc

...be sure to check for this issue/upgrade: https://github.com/jgarzik/python-bitcoinrpc/issues/62

Also requires python QR Code: https://github.com/mnooner256/pyqrcode

Add this line to bitcoin.conf:

`blocknotify=python /PATH TO YOUR DIRECTORY/block.py %s`

these lines also help with running a full node on a Raspberry Pi:

`minrelaytxfee=0.00005000`

`limitfreerelay=0`

`dbcache=50`

And create a file called bitcoinAuth.py in your directory with:

`USER = "your RPC user name"`

`PW = "your RPC password"`
