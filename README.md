requires python-bitcoinrpc https://github.com/jgarzik/python-bitcoinrpc

add this line to bitcoin.conf:
`blocknotify=python /home/pi/pybits/block.py %s`

create a file called bitcoinAuth.py with:
`USER = "your RPC user name"`
`PW = "your RPC password"`
