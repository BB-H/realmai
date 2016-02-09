# -*- coding: utf-8 -*-
import scrapy
import logging
from scrapy.utils.response import get_base_url
from scrapy.utils.url import urljoin_rfc
from scrapy.http import Request
from mybid.items import JDItem


#logger = logging.getLogger("jdLogger")

class JdSpider(scrapy.Spider):
	# --self defined variables --#
	HTTP_SITE_ROOT = "http://www.jd.com"
	root_url = HTTP_SITE_ROOT+"/allSort.aspx"
	TYPE_LIST_PAGE = "http://list.jd.com/list.html?"
	TYPE_ITEM_PAGE = "http://item.jd.com"
	MAX_LIST_PAGE = 50 #指定某一个list页抓取的最大页数
	#allUrlSet = set()
	allReachedUrls = set()
	
	name = "jd"
	allowed_domains = ["jd.com"]
	start_urls = [
		root_url,
	]
	
	def parse(self,resp):
		if resp.url == self.root_url:
			links = resp.xpath('//a/@href').extract()
			for link in links:
				if not link.strip().lower().startswith("http://"):
					link = self.toFullURL(resp,link)
				if link.startswith(self.TYPE_LIST_PAGE):
					req = Request(link,self.parseUrl)
					req.meta['depth']=1
					yield req
		
	
	def parseUrl(self,resp):
		self.allReachedUrls.add(resp.url)
		if resp.url.startswith(self.TYPE_LIST_PAGE):
			#1. deal with all items in the list page
			links = resp.xpath('//*[@id="plist"]/ul/li/div/div[1]/a/@href').extract()
			for link in links:
				if not link.strip().lower().startswith("http://"):
					link = self.toFullURL(resp,link)
				if link in self.allReachedUrls:
					continue
				req = Request(link,self.parseUrl)
				req.meta['PhantomJS'] = True
				yield req
				
				'''
				if (link.startswith(self.TYPE_LIST_PAGE) and resp.meta['depth'] <= self.MAX_LIST_PAGE) or \
				link.startswith(self.TYPE_ITEM_PAGE):
					req = Request(link,self.parseUrl)
					req.meta['depth'] = resp.meta['depth']+1
					if link.startswith(self.TYPE_ITEM_PAGE):
						req.meta['PhantomJS'] = True
					yield req
				'''
			#2. deal with next page
			if resp.meta['depth'] <= self.MAX_LIST_PAGE:
				theNextPage = ""
				#get all the links which is after the current page
				selectors = resp.xpath('//*[@id="J_bottomPage"]/span[1]/a[@class="curr"]/following-sibling::a')
				for selector in selectors:
					#only the link which has empty class and first time appears after current link is the next page.
					classVal = selector.xpath('@class')[0].extract().encode("utf-8")
					if classVal.strip() == "":
						theNextPage = selector.xpath('@href')[0].extract().encode('utf-8')
						break
				if theNextPage != "":
					theNextPage = self.toFullURL(resp,theNextPage)
					req = Request(theNextPage,self.parseUrl)
					req.meta['depth'] = resp.meta['depth']+1
					yield req
			else:
				logging.info("Reached max page deepth, ending crawling.")
		if resp.url.startswith(self.TYPE_ITEM_PAGE):
			#logging.info("DEAL WITH ITEM PAGE:"+resp.url)
			item_name = resp.xpath('//*[@id="name"]/h1/text()')[0].extract().encode("utf-8")
			item_id = resp.xpath('//*[@id="short-share"]/div/span[2]/text()')[0].extract().encode("utf-8")
			item_price = resp.xpath('//*[@id="jd-price"]/text()')[0].extract().encode("utf-8")[3:]#price example:￥5288.00
			item = JDItem()
			item['jdId'] = item_id
			item['name'] = item_name
			item['price'] = item_price
			item['itemLink'] = resp.url
			yield item
	
	
	def toFullURL(self,response,url):
		if not url.startswith("http://"):
			return urljoin_rfc(get_base_url(response),url.strip())
		else:
			return url