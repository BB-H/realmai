# -*- coding: utf-8 -*-
from scrapy.http import HtmlResponse
from scrapy.http import Request
import os, logging, traceback, random
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from mybid.HttpProxyFactory import HttpProxyFactory

from scrapy.utils.project import get_project_settings

import MySQLdb

SETTINGS = get_project_settings()

class PhantomJSMiddleware(object):  

	user_agents = [
				("Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.103 Safari/537.36"),
				("Mozilla/4.0 (compatible; MSIE 6.0; America Online Browser 1.1; Windows NT 5.1; SV1; .NET CLR 1.0.3705; .NET CLR 1.1.4322; Media Center PC 3.1)"),
				("Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/527+ (KHTML, like Gecko, Safari/419.3) Arora/0.4 (Change: )"),
				("Mozilla/5.0 (Windows; U; Windows NT 5.2) AppleWebKit/525.13 (KHTML, like Gecko) Version/3.1 Safari/525.13"),
				("Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10"),
	]
	
	dcap = dict(DesiredCapabilities.PHANTOMJS)
	dcap["phantomjs.page.settings.userAgent"] = random.choice(user_agents)

	def __init__(self):
		self.proxyFactory = HttpProxyFactory.getHttpProxyFactory()

	# overwrite process request  
	def process_request(self, request, spider):
		if request.meta.has_key('PhantomJS'):# 
			logging.info('[PID:%s] PhantomJS Requesting: %s' %(os.getpid(),request.url))  
			proxy = self.proxyFactory.getRandomProxy()
			if proxy:
				driver = self.getProxiedDriver(proxy)
			else:
				driver = self.getDriver()
			try:
				driver.get(request.url)
				wait = WebDriverWait(driver, 10)#设置超时时长
				wait.until(EC.visibility_of_element_located((By.ID, 'jd-price')))#直到jd-price元素被填充之后才算请求完成
				content = driver.page_source.encode('utf-8')
				url = driver.current_url.encode('utf-8') 
				if content is None or content.strip()=="" or content == '<html><head></head><body></body></html>':# 
					logging.debug("[PID:%s] PhantomJS Request failed!" %os.getpid())
					return HtmlResponse(request.url, encoding = 'utf-8', status = 503, body = '')  
				else: # 
					logging.debug("[PID:%s]PhantomJS Request success!" %os.getpid())
					return HtmlResponse(url, encoding = 'utf-8', status = 200, body = content) 
			except Exception as e: 
				errorStack = traceback.format_exc()
				logging.error('[PID:%s] PhantomJS request exception! exception info:%s'%(os.getpid(),errorStack))
				return HtmlResponse(request.url, encoding = 'utf-8', status = 503, body = '')
			finally:
				driver.quit()
	
	def getProxiedDriver(self, proxy):
		service_args = [
			'--proxy=%s' %proxy,
			'--proxy-type=http',
			'--load-images=false'
			]
		return webdriver.PhantomJS(executable_path = '/usr/local/bin/phantomjs',desired_capabilities=self.dcap,service_args=service_args,)
	
	def getDriver(self):
		service_args = [
			'--load-images=false'
			]
		driver = webdriver.PhantomJS(executable_path = '/usr/local/bin/phantomjs',desired_capabilities=self.dcap,service_args=service_args,)
		return driver
 


class ItemFilterMiddleware(object):
	'''
	This is a spider middleware that is used to filter and drop the request which already exists in DB. 
	'''
	TYPE_ITEM_PAGE = "http://item.jd.com"
	
	def __init__(self):
		self.db = MySQLdb.connect(host=SETTINGS['DB_HOST'],
						user=SETTINGS['DB_USER'],
						passwd=SETTINGS['DB_PASSWD'],
						db=SETTINGS['DB_DB'])
		self.cur = self.db.cursor()
	
	def __del__(self):
		self.db.close()
	
	def process_spider_output(self,response, result, spider):
		for r in result:
			if isinstance(r,Request) and r.url.startswith(self.TYPE_ITEM_PAGE):
				#sql = "SELECT id from JD_Item where item_link = '%s'" %r.url.strip()
				sql = "SELECT id from JD_Item where item_link = %s" #%r.url.strip()
				self.cur.execute(sql,(r.url.strip(),))
				if len(self.cur.fetchall())==0:
					yield r
				else:
					logging.info('[PID:%s]The URL exists in DB, skip it: %s' %(os.getpid(),r.url))
			else:
				yield r
