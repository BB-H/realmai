# -*- coding: utf-8 -*-
from scrapy.http import HtmlResponse
from scrapy.http import Request
import logging, traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

#logger = logging.getLogger("jdLogger")

class PhantomJSMiddleware(object):  
	# overwrite process request  
	def process_request(self, request, spider):
		if request.meta.has_key('PhantomJS'):# 
			logging.info('PhantomJS Requesting: '+request.url)  
			service_args = ['--load-images=false', '--disk-cache=true']  
			#if request.meta.has_key('proxy'): # 如果设置了代理(由代理中间件设置)
			#	logging.info('PhantomJS proxy:'+request.meta['proxy'][7:])  
			#	service_args.append('--proxy='+request.meta['proxy'][7:])  
			try:  
				driver = webdriver.PhantomJS(executable_path = '/usr/local/bin/phantomjs', service_args = service_args,)  
				driver.get(request.url)
				wait = WebDriverWait(driver, 10)#设置超时时长
				wait.until(EC.visibility_of_element_located((By.ID, 'jd-price')))#直到jd-price元素被填充之后才算请求完成
				#wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, '.archive_loading_bar')))
				#price =  "######>>> URL:%s,PRICE:%s ###" %(request.url,driver.find_element_by_id('jd-price').text.encode('utf-8'))
				content = driver.page_source.encode('utf-8')
				url = driver.current_url.encode('utf-8') 
				driver.quit()  
				if content == '<html><head></head><body></body></html>':# 
					logging.debug("PhantomJS Request failed!")
					return HtmlResponse(request.url, encoding = 'utf-8', status = 503, body = '')  
				else: # 
					logging.debug("PhantomJS Request success!")
					return HtmlResponse(url, encoding = 'utf-8', status = 200, body = content) 
			except Exception as e: 
				print e
				errorStack = traceback.format_exc()
				logging.error('PhantomJS request exception! exception info:%s'%errorStack)
				return HtmlResponse(request.url, encoding = 'utf-8', status = 503, body = '')  
 