#!/usr/bin/env python
#coding=utf-8

import re, sys, time, commands, threading, json, urllib2, MySQLdb
from datetime import datetime
sys.path.append("..")
from config.sql import sqlinit
interval_ws = 300
interval_bsy = 300
bwtable = 'bandwidth'
headers_test = {'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6'}
# 调cdn接口

def ws_query():
	while True:
		atime = datetime.utcnow()
		cdnseller = "wangsu"
		timenow = int(time.time()) - 60*3
	        stime = time.strftime("%Y-%m-%d %H:%M", time.localtime(timenow - 300)).replace(' ','%20')
        	etime = time.strftime("%Y-%m-%d %H:%M", time.localtime(timenow)).replace(' ','%20')
	        url_test = "https://myview.chinanetcenter.com/api/bandwidth-channel.action?u=username&p=password&startdate=%s&enddate=%s&dataformat=json" % (stime, etime)
        	req_test = urllib2.Request(url = url_test, headers = headers_test)
		try:
	        	result_test = urllib2.urlopen(req_test)
        		res = result_test.read()
	        	bandwidthdata = eval(res)["provider"]["date"]["channel"]["bandwidth"]
                except Exception,e:
                        continue
		if type(bandwidthdata) == list :
			bandwidthdata = bandwidthdata[-1]
		print bandwidthdata
		bwsize = round(float(bandwidthdata['text']),2)
		if bwsize == 0.0:
			continue
		bwtime = bandwidthdata['time']
		if re.findall('24:00:00',bwtime) != []:
        		bwtime = bwtime.replace('24:00:00','23:59:59')
        		fbwtime = time.mktime(time.strptime(bwtime,'%Y-%m-%d %H:%M:%S')) + 1
		else:
        		fbwtime = time.mktime(time.strptime(bwtime,'%Y-%m-%d %H:%M:%S'))
		sql = "INSERT INTO %s (`cdnseller`,`time`,`data`) VALUES('%s', '%s', '%s')" % (bwtable, cdnseller, fbwtime, bwsize)
		print sql
		sqlinit(sql)
		status, localoutput = commands.getstatusoutput('/data1/xinsrv/zabbix/bin/zabbix_sender  -z x.x.x.x -s "x.x.x.x" -k cdn.ws.net -o %s' % bwsize)
		btime = datetime.utcnow()
		time.sleep(interval_ws - ((btime - atime).total_seconds()))

def bsy_query():
	while True:	
		atime = datetime.utcnow()
		cdnseller = "baishanyun"
		timenow = int(time.time()) - 60*4
		start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timenow - 60*5))
        	end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timenow))
        	print start_time, end_time
        	url_test = 'http://api.qingcdn.com/apix'
        	data_test = {
		"token": "97c808xxxxxxxxxxxxxxxxxxx",
        	"method": "bandwidth.get",
        	"params": {
	        	"domains": [
				"test1.domain.com",
				"test2.domain.com",
      	  			],
        	"start_time": start_time,
        	"end_time": end_time
        	}
	}
        	djson_test = json.dumps(data_test)
        	req_test = urllib2.Request(url_test, djson_test, {'Content-Type': 'application/json'}, headers_test)
		try:
        		res = urllib2.urlopen(req_test)
			resdata = eval(res.read())
			print 'resdata: ', resdata
			qtime = resdata['data'][-1][0]
			qdata = resdata['data'][-1][1]
                except Exception,e:
                        continue
		qdata = round(float(qdata)/1024/1024,2)
		if qdata == 0.0:
			continue
		sql = "INSERT INTO %s (`cdnseller`,`time`,`data`) VALUES('%s', '%s', '%s')" % (bwtable, cdnseller, qtime, qdata)
		print "sql :", sql
		sqlinit(sql)	
		status, localoutput = commands.getstatusoutput('/data1/xinsrv/zabbix/bin/zabbix_sender  -z x.x.x.x -s "x.x.x.x" -k cdn.bsy.net -o %s' % qdata)
		btime = datetime.utcnow()
		time.sleep(interval_bsy - ((btime - atime).total_seconds()))

tbsy=threading.Thread(target = bsy_query,args = () )
tbsy.start()
tws=threading.Thread(target = ws_query,args = () )
tws.start()


