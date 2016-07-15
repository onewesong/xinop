#!/usr/bin/env python
#coding=utf-8

import sys
reload(sys)
sys.setdefaultencoding('utf8')
sys.path.append("..")

import json
import MySQLdb as mysql
from flask import Flask,request,render_template,Blueprint
from config.sql import sqlinit
cdnpg = Blueprint('ckmon',__name__,template_folder='templates',static_folder='static')

@cdnpg.route("/cdn/bwindex", methods = ["GET", "POST"])
def cdnindex():
        return render_template("cdnpages/cdnindex.html")

@cdnpg.route("/cdn/bwmondata", methods = ["GET"])
def cdnbwquery():
	ret = {}
	for cdnseller in ['baishanyun', 'wangsu']:
		sql = "SELECT count(*) FROM `bandwidth` where cdnseller = '%s' " % cdnseller
		dn = sqlinit(sql)
		linedata = int(dn[0][0])
		memdata = []
		callbackdata = request.args.get('ctest')
		if linedata >= 2000:
			linestart = linedata - 2000
			# 取最后2000条数据
			sql = "SELECT `time`,`data` FROM `bandwidth` where cdnseller = '%s' limit %d,2000" % (cdnseller, linestart)
			datainfo = sqlinit(sql)
			#print 'datainfo: ',datainfo
			for i in datainfo:
				memdata.append([i[0]*1000, float(i[1])])
			ret[cdnseller] = memdata
		else:
			sql = "SELECT `time`,`data` FROM `bandwidth` where cdnseller = '%s'"  % cdnseller
			datainfo = sqlinit(sql)
			for i in datainfo:
				memdata.append([i[0]*1000, float(i[1])])
			ret[cdnseller] = memdata
	return "%s(%s);" % (callbackdata, json.dumps(ret))
		
