#!/usr/bin/env python
#coding=utf-8
import ldap

# ldap 服务器端口，用户密码
class ldap_xin():
        def __init__(self, ldap_who, ldap_cred):
                self.ldap_host = "x.x.x.x"
                self.ldap_port = 389
                self.ldap_who = "xxx" + "\\" + ldap_who
                self.ldap_cred = ldap_cred
                self.ldap_baseondn = "OU=xxx,DC=xxx,DC=xxx,DC=xxx"
                self.filterwd = 'samaccountname=' + ldap_who + '*'
		self.ret = {}
        def check(self):
                # 连接ldap
                l = ldap.open(self.ldap_host, self.ldap_port)
		try:
                	l.simple_bind_s(self.ldap_who, self.ldap_cred)
		except ldap.INVALID_CREDENTIALS:
			self.ret["authcode"] = "-1"
			return self.ret
			#return 'username or passwd error1...'
                result_id = l.search(self.ldap_baseondn, ldap.SCOPE_SUBTREE, self.filterwd, None)
		try:
			result_type, result_data = l.result(result_id, 0)
		except ldap.OPERATIONS_ERROR:
			self.ret["authcode"] = "-1"
			return self.ret
		zhname = result_data[0][0].split(',')[0].split('=')[1]
		self.ret["authcode"] = "1"
		self.ret["userzhname"] = zhname
                return self.ret


