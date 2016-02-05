import time
import bitcoinAuth
import thread
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

rpc_connection = AuthServiceProxy("http://%s:%s@127.0.0.1:8332"%(bitcoinAuth.USER,bitcoinAuth.PW))

def mp():
	print rpc_connection.getmempoolinfo()

def pr():
	print rpc_connection.getpeerinfo()
	
def ux():
	print rpc_connection.gettxoutsetinfo()
	
def gi():
	print rpc_connection.getinfo()

count = 0
while True:
	print "++", count, "++"
	if (count%10 == 0):
		print rpc_connection.getmempoolinfo()

	'''
		try:
			thread.start_new_thread(mp,())
			#thread.start_new_thread(pr,())
			#thread.start_new_thread(ux,())
			#thread.start_new_thread(gi,())
		except:
			print "E!"
	count += 1
	time.sleep(0.5)
	'''