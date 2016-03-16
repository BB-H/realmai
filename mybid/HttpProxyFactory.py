# -*- coding: utf-8 -*-

import socket, time, thread, logging, os
import urllib2
import threading
import random
import time
from multiprocessing.dummy import Pool as ThreadPool
#from phantomJsTool import PhantomJS as PhantomJSService


class HttpProxyFactory(object):
	
	TEST_PAGE_BING = "http://cn.bing.com/"
	TEST_PAGE_JD = "http://www.jd.com/"
	MAX_THREAD = 100
	ENABLE_PROXY = True
	allProxySet=set()
	newProxyList = []
	validProxyList = []
	lock = threading.Lock()
	proxyLock = threading.Lock()
	refreshLock = threading.Lock()
	__instance = None
	

	def __init__(self):
		self.refreshProxies()
		print("Available proxies are %s" %len(HttpProxyFactory.validProxyList))
		timer = threading.Timer(60*30, self.refreshScheduler)
		timer.start()
		
	def refreshScheduler(self):
		logging.info("[PID:%s] Refreshing proxy list..." %os.getpid())
		self.refreshProxies()
		timer = threading.Timer(60*60, self.refreshScheduler)
		timer.start()
	
	
	def refreshProxies(self):
		proxyFile = os.path.join("proxy.list")
		if os.path.isfile(proxyFile):
			f = file(proxyFile, 'r')
			HttpProxyFactory.allProxySet = set()
			for line in f.readlines():
				line = line.strip()
				if len(line)>0:
					HttpProxyFactory.allProxySet.add(line)
			f.close()
		print("All proxies are:%s" % len(HttpProxyFactory.allProxySet))
		HttpProxyFactory.newProxyList = []
		if HttpProxyFactory.allProxySet:
			threadAmount = max(len(HttpProxyFactory.allProxySet)/5,2)
			threadAmount = min(threadAmount,HttpProxyFactory.MAX_THREAD)
			pool = ThreadPool(threadAmount)
			pool.map(self.checkProxyAvailable,HttpProxyFactory.allProxySet)
			pool.close() 
			pool.join()
		HttpProxyFactory.proxyLock.acquire()
		HttpProxyFactory.validProxyList = HttpProxyFactory.newProxyList
		HttpProxyFactory.proxyLock.release()
		
	
	def checkProxyAvailable(self,ipAndPort):
		try:
			for i in [1,2,3]: #Check avaliability for 3 times
				proxy_handler = urllib2.ProxyHandler({'http': ipAndPort})
				opener = urllib2.build_opener(proxy_handler)
				opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.103 Safari/537.36')]
				urllib2.install_opener(opener)
				req=urllib2.Request(HttpProxyFactory.TEST_PAGE_JD)
				req.add_header('Cache-Control', 'max-age=0')
				response = urllib2.urlopen(req,timeout=2.5)
				html = response.read()
				if html.find('id="focus"')<0 and html.find("id='focus'")<0: #amazon.cn login element
					return
				time.sleep(2)
			HttpProxyFactory.refreshLock.acquire()
			print '[VALID] %s' % ipAndPort
			HttpProxyFactory.newProxyList.append(ipAndPort)
			HttpProxyFactory.refreshLock.release()
		except urllib2.HTTPError:
			print '[INVALID] %s' % ipAndPort
		except Exception:
			print '[INVALID] %s' % ipAndPort
	
	def getRandomProxy(self):
		proxy = None
		HttpProxyFactory.proxyLock.acquire()
		if len(HttpProxyFactory.validProxyList)>0:
			proxy = random.choice(HttpProxyFactory.validProxyList)
			logging.debug("Get a random Http proxy(1/%s):%s" %(len(HttpProxyFactory.validProxyList),str(proxy)))
		HttpProxyFactory.proxyLock.release()
		return proxy

		
	def getValidProxyAmount(self):
		return len(HttpProxyFactory.validProxyList)

	@staticmethod
	def getHttpProxyFactory():
		HttpProxyFactory.lock.acquire()
		if HttpProxyFactory.__instance is None:
			HttpProxyFactory.__instance = HttpProxyFactory()
		HttpProxyFactory.lock.release()
		return HttpProxyFactory.__instance
	
	def wrapWithProxy(self,request):
		if not HttpProxyFactory.ENABLE_PROXY:
			return
		proxy = self.getRandomProxy()
		if proxy:
			request.meta['proxy'] = "http://"+proxy
	
	
if __name__ == '__main__':
	#factory = HttpProxyFactory()
	
	
	f = file('valid-proxy.list','w')
	f.writelines("\n".join(HttpProxyFactory.getHttpProxyFactory().validProxyList))
	f.close()
	



