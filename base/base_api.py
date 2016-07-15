#!/usr/bin/env python
#coding=utf-8
 
import urllib2, urllib, json, re, sys, os
 
class saltAPI:
	def __init__(self):
        	self.__url = 'https://x.x.x.x:8000'       #salt-api监听的地址和端口
        	self.__user =  'username'             #salt-api用户名
        	self.__password = 'passwd'          #salt-api用户密码
        	self.__token_id = self.salt_login()
 
	def salt_login(self):
        	params = {'eauth': 'pam', 'username': self.__user, 'password': self.__password}
        	encode = urllib.urlencode(params)
        	obj = urllib.unquote(encode)
        	headers = {'X-Auth-Token':''}
        	url = self.__url + '/login'
        	req = urllib2.Request(url, obj, headers)
        	opener = urllib2.urlopen(req)
        	content = json.loads(opener.read())
        	try:
        		token = content['return'][0]['token']
        		return token
		except KeyError:
                	raise KeyError
 
	def postRequest(self, obj, prefix='/'):
        	url = self.__url + prefix
        	headers = {'X-Auth-Token'   : self.__token_id}
        	req = urllib2.Request(url, obj, headers)
        	opener = urllib2.urlopen(req)
        	content = json.loads(opener.read())
        	return content['return']
 
	def saltCmd(self, params):
        	obj = urllib.urlencode(params)
        	obj, number = re.subn("arg\d", 'arg', obj)
        	res = self.postRequest(obj)
        	return res
 
def chenkun(cmdclass,serverkey,cmdname):
#def chenkun(cmdclass,sername,cmdname,minionsqueue):
        #以下是用来测试saltAPI类的部分
	sapi = saltAPI()
	#params = {'client':'local', 'fun':'cmd.run', 'tgt':'*', 'arg':'w'}
	#params = {'client':'local', 'fun':cmdclass, 'tgt':sername, 'arg':cmdname, 'expr_form':'nodegroup'}
	params = {'client':'local', 'fun':cmdclass, 'tgt':serverkey, 'arg':cmdname}
	#params = {'client':'local', 'fun':'test.echo', 'tgt':'某台服务器的key', 'arg1':'hello'}
	#params = {'client':'local', 'fun':'test.ping', 'tgt':'某组服务器的组名', 'expr_form':'nodegroup'}
	test = sapi.saltCmd(params)
	return test

