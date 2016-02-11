# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html


import MySQLdb.cursors
from twisted.enterprise import adbapi

from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals
from scrapy.utils.project import get_project_settings
import os, logging

#logger = logging.getLogger("jdLogger")

class MybidPipeline(object):
	def process_item(self, item, spider):
		return item

SETTINGS = get_project_settings()

class MySQLPipeline(object):

	@classmethod
	def from_crawler(cls, crawler):
		return cls(crawler.stats)

	def __init__(self, stats):
		#Instantiate DB
		self.dbpool = adbapi.ConnectionPool ('MySQLdb',
			host=SETTINGS['DB_HOST'],
			user=SETTINGS['DB_USER'],
			passwd=SETTINGS['DB_PASSWD'],
			port=SETTINGS['DB_PORT'],
			db=SETTINGS['DB_DB'],
			charset='utf8',
			use_unicode = True,
			cursorclass=MySQLdb.cursors.DictCursor
		)
		self.stats = stats
		dispatcher.connect(self.spider_closed, signals.spider_closed)
	def spider_closed(self, spider):
		""" Cleanup function, called after crawing has finished to close open
			objects.
			Close ConnectionPool. """
		self.dbpool.close()

	def process_item(self, item, spider):
		query = self.dbpool.runInteraction(self.__insert_if_not_exist, item)
		query.addErrback(self._handle_error)
		return item

	def isExist(self,item):
		sql = "SELECT id from JD_Item where jd_id = '%s'" %item['jdId']
		result = tx.execute(sql)
		if result > 0:
			return True
		else:
			return False

	def __insert_if_not_exist(self,tx,item):
		sql = "SELECT id from JD_Item where jd_id = '%s'" %item['jdId']
		res = tx.execute(sql)
		if res == 0:
			logging.info("[PID:%s]Insert JD item (jdID=%s)." %(os.getpid(),item['jdId']))
			sql = "INSERT INTO JD_Item (jd_id,name,item_price,item_link) VALUES ('%s','%s','%s','%s')"%(item['jdId'],item['name'],item['price'],item['itemLink'])
			#result = tx.execute(""" INSERT INTO JD_Item (jd_id,name) VALUES (item['jdId'],item['name'])""") 
			result = tx.execute(sql)
			if result > 0:
				self.stats.inc_value('database/items_added')
		else:
			logging.info("[PID:%s]Duplicated item(jdID=%s), ignore it!" %(os.getpid(),item['jdId']))
		
	
	def _insert_record(self, tx, item):
		sql = "INSERT INTO JD_Item (jd_id,name,item_price,item_link) VALUES ('%s','%s','%s','%s')"%(item['jdId'],item['name'],item['price'],item['itemLink'])
		#result = tx.execute(""" INSERT INTO JD_Item (jd_id,name) VALUES (item['jdId'],item['name'])""") 
		result = tx.execute(sql)
		if result > 0:
			self.stats.inc_value('database/items_added')

	def _handle_error(self, e):
		logging.error("[PID:%s] DB operating ERROR:%s" %(os.getpid(),e))  