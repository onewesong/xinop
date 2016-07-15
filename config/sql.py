#!/usr/bin/env python
#coding=utf-8

import MySQLdb
def sqlinit(sql):
	conn = MySQLdb.connect(host = 'x.x.x.x', port = 3306, user = 'username', passwd = 'password', db = 'xinop', charset = 'utf8')
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()
        conn.close()
        rz = cur.fetchall()
        cur.close()
        return rz

