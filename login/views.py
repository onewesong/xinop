#!/usr/bin/env python
#coding=utf-8
import sys
reload(sys)
sys.setdefaultencoding('utf8')

import json
from flask import Flask,request,render_template,Blueprint,redirect,session
from ldap_class import ldap_xin
loginpg = Blueprint('loginbp',__name__,template_folder='templates',static_folder='static')

@loginpg.route("/login/", methods = ["POST","GET"])
def login():
        if request.method == 'GET':
                return render_template('loginpages/login.html')
        elif request.method == 'POST':
                udata = request.json
                uname = udata['username'].encode('utf-8')
                upasswd = udata['password'].encode('utf-8')
		o = {}
		loginret = ldap_xin(uname, upasswd).check()
		if loginret["authcode"] == "1":
			o['status'] = 'uok'
			o['yourname'] = loginret["userzhname"]
			session['username'] = loginret["userzhname"]
			session['password'] = upasswd
		elif loginret["authcode"] == "-1":
			o['status'] = 'uerror'
		return json.dumps(o)

@loginpg.route("/logout/")
def logout():
        session.pop('username',None)
        session.pop('password',None)
        return redirect('/login/')

