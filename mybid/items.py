# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class MybidItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass
	
class JDItem(scrapy.Item):
	id = scrapy.Field()
	name = scrapy.Field()
	jdId =  scrapy.Field()
	price = scrapy.Field()
	itemLink = scrapy.Field()
	
	'''
	def __init__(self,name,jdId,price,itemLink):
		self.name = name
		self.jdId = jdId
		self.price = price
		self.itemLink = itemLink 
	'''
