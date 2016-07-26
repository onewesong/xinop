#!/usr/bin/env python
#coding=utf-8
 
import urllib2, urllib, json, re, sys, os
 
class saltAPI:
	def __init__(self):
                self.__url = 'https://x.x.x.x:8000' 
                self.__user =  'xxx'             #salt-api用户名
                self.__password = 'xxx'          #salt-api用户密码
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
 
def chenkun(cmdclass,sername,cmdname,minionsqueue):
	sapi = saltAPI()
	params = {'client':'local', 'fun':cmdclass, 'tgt':sername, 'arg':cmdname}
	test = sapi.saltCmd(params)
	html_data = ''
	for i in test[0]:
		html_data = html_data + '''<p style="color:#009100; font-weight:bold; font-size:16px">%s</p>\n %s \n''' % (i,test[0][i])
	fsalt=file('saltres.txt','w')
        fsalt.write(html_data)
        fsalt.close()
	os.system('sed -i "/^<p/! {s/^/<p>/;s/$/<p>/;{s/u\'//g;s/\'//g}}" saltres.txt')
	ck_queue = minionsqueue
	ck_queue.put(test[0].keys())


