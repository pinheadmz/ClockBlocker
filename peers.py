#!/usr/bin/env python

################
# dependencies #
################

import sys
import os
import urllib2
import json
import bitcoinAuth
import ipInfoAuth
import time
from bitcoinrpc import AuthServiceProxy, JSONRPCException


#############
# constants #
#############

rootdir = sys.path[0]
peerFile =  rootdir + '/data/peer_list.txt'

##############
# initialize #
##############

# initialize bitcoin RPC connection and gather info
rpc_connection = AuthServiceProxy("http://%s:%s@127.0.0.1:8332"%(bitcoinAuth.USER,bitcoinAuth.PW))


#############
# functions #
#############

# refresh the peers list
def refreshPeers():
	# create new file if missing
	if not os.path.isfile(peerFile):
		# create directory if missing
		if not os.path.exists(rootdir + '/data'):
			os.makedirs(rootdir + '/data')
			os.chmod(rootdir + '/data', 0777)
		
		p = os.open(peerFile, os.O_CREAT)
		# script will be run both as root and user
		os.fchmod(p, 0777)
		os.close(p)

	# open file and read data
	p = open(peerFile, 'r+')
	oldPeerData = p.read()
	if oldPeerData:
		peerDataJson = json.loads(oldPeerData)
	else:
		peerDataJson = json.loads("{}")
	
	# move file pointer back to top
	p.seek(0)

	# get peerinfo from bitcoind
	updatedPeers = []
	newPeerInfo = rpc_connection.getpeerinfo()
	newPeers = 0
	totalPeers = 0

	headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '
      'AppleWebKit/537.11 (KHTML, like Gecko) '
      'Chrome/23.0.1271.64 Safari/537.11',
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
      'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
      'Accept-Encoding': 'none',
      'Accept-Language': 'en-US,en;q=0.8',
      'Connection': 'keep-alive'}

	# request location from IP info server and fill out info for display
	for peer in newPeerInfo:
		totalPeers += 1
		thisPeer = {}
		thisPeer['addr'] = peer['addr']
		thisPeer['inbound'] = peer['inbound']
		thisPeer['subver'] = peer['subver']
		
		# do we need to reload this IP info? Check for per, then check we have its info
		checkForOld = next((item for item in peerDataJson if item["addr"] == thisPeer['addr']), False)
		if checkForOld:
			if ('country' in checkForOld and checkForOld['country']):
				updatedPeers.append(checkForOld)
				continue
		
		# get the location info from IP API
		thisIP = thisPeer['addr'].split(':')[0]
		
		try:
			response = urllib2.urlopen(urllib2.Request('https://api.ipinfodb.com/v3/ip-city/?key=' + ipInfoAuth.api_key   + '&format=json&ip=' + thisIP, headers=headers))
		except Exception as e:
			# print(e)
			response = False	
		
		if response:
			# print(response)
			responseJson = json.load(response)	
			newPeers += 1
		else:
			# print("no response")
			responseJson = False
		
		thisPeer['country'] = responseJson['countryName'] if response else ''
		thisPeer['region'] = responseJson['regionName'] if response else ''
		thisPeer['city'] = responseJson['cityName'] if response else ''
		
		updatedPeers.append(thisPeer)
		time.sleep(0.5)
	
	# write json of peer info and close
	peerJson = json.dumps(updatedPeers)	
	p.write(peerJson)
	p.truncate()
	p.close()
	return "Peers list refreshed: " + str(newPeers) + " updated, " + str(totalPeers) + " total"

if __name__ == "__main__":
	print("refreshing...")
	res = refreshPeers()
	print(res)
