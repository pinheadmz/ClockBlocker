import bitcoinAuth
from bitcoinrpc import AuthServiceProxy, JSONRPCException


rpc_connection = AuthServiceProxy("http://%s:%s@127.0.0.1:8332"%(bitcoinAuth.USER,bitcoinAuth.PW))

addr = rpc_connection.getnewaddress()
print addr