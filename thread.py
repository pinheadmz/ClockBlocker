import sys, select, tty, termios, time

# capture current terminal settings before setting to one character at a time
old_settings = termios.tcgetattr(sys.stdin)

try:
	# one char at a time, no newline required
	tty.setcbreak(sys.stdin.fileno())

	count = 0
	while True:
		print "++", count, "++"
		count += 1
		if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
			print "!:", sys.stdin.read(1), ":!"
		time.sleep(0.5)
finally:
	# reset terminal settings to normal expected behavior
	termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
    
    

'''
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