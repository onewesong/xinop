#!/usr/bin/env python
#coding=utf-8

from flask import Flask,render_template,request,redirect,make_response
import os,MySQLdb
### 使页面识别中文
import sys
reload(sys)
sys.setdefaultencoding('utf8')
###
from ckcmdb.views import cmdbpg
from orsync.views import orsyncpg
from cdn.views import cdnpg
from zbxquery.views import zbxpg

cktest=Flask(__name__)
cktest.register_blueprint(cmdbpg)
cktest.register_blueprint(orsyncpg)
cktest.register_blueprint(cdnpg)
cktest.register_blueprint(zbxpg)

if __name__=='__main__':
	cktest.run(host="0.0.0.0", port=8888)

