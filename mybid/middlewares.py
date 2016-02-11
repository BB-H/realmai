# -*- coding: utf-8 -*-
from scrapy.http import HtmlResponse
from scrapy.http import Request
import os, logging, traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from scrapy.utils.project import get_project_settings

import MySQLdb

SETTINGS = get_project_settings()

class PhantomJSMiddleware(object):  
	# overwrite process request  
	def process_request(self, request, spider):
		if request.meta.has_key('PhantomJS'):# 
			logging.info('[PID:%s] PhantomJS Requesting: %s' %(os.getpid(),request.url))  
			service_args = ['--load-images=false', '--disk-cache=true']  
			#if request.meta.has_key('proxy'): # 如果设置了代理(由代理中间件设置)
			#	logging.info('PhantomJS proxy:'+request.meta['proxy'][7:])  
			#	service_args.append('--proxy='+request.meta['proxy'][7:])  
			driver = webdriver.PhantomJS(executable_path = '/usr/local/bin/phantomjs', service_args = service_args,)
			try:
				driver.get(request.url)
				wait = WebDriverWait(driver, 5)#设置超时时长
				wait.until(EC.visibility_of_element_located((By.ID, 'jd-price')))#直到jd-price元素被填充之后才算请求完成
				#wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, '.archive_loading_bar')))
				#price =  "######>>> URL:%s,PRICE:%s ###" %(request.url,driver.find_element_by_id('jd-price').text.encode('utf-8'))
				content = driver.page_source.encode('utf-8')
				url = driver.current_url.encode('utf-8') 
				if content == '<html><head></head><body></body></html>':# 
					logging.debug("[PID:%s] PhantomJS Request failed!" %os.getpid())
					return HtmlResponse(request.url, encoding = 'utf-8', status = 503, body = '')  
				else: # 
					logging.debug("[PID:%s]PhantomJS Request success!" %os.getpid())
					return HtmlResponse(url, encoding = 'utf-8', status = 200, body = content) 
			except Exception as e: 
				print e
				errorStack = traceback.format_exc()
				logging.error('[PID:%s] PhantomJS request exception! exception info:%s'%(os.getpid(),errorStack))
				return HtmlResponse(request.url, encoding = 'utf-8', status = 503, body = '')
			finally:
				driver.quit()
 


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
				sql = "SELECT id from JD_Item where item_link = '%s'" %r.url.strip()
				self.cur.execute(sql)
				if len(self.cur.fetchall())==0:
					yield r
				else:
					logging.info('[PID:%s]The URL exists in DB, skip it: %s' %(os.getpid(),r.url))
			else:
				yield r
