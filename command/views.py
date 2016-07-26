#!/usr/bin/env python
#coding=utf-8
from flask import Flask,request,render_template,Blueprint,session,redirect
import sys,os,commands,re,time,json,Queue
import MySQLdb as mysql
### 使页面识别中文
reload(sys)
sys.setdefaultencoding('utf8')
sys.path.append("..")
from config.sql import sqlinit
from salt_api import chenkun

###
commandpg = Blueprint('commandbp',__name__,template_folder='templates',static_folder='static')
minionsdir = "/etc/salt/pki/master/minions/"

@commandpg.route('/command/history/')
def commandhistory():
	querytime = request.args.get('qtime')
	gotopage = int(request.args.get('qpage',1))
	count = request.args.get('count',10)
	ntime = int(time.time())
	o = {
        'status':0,
        'li_str':'',
        'pagation_str':''
	}   

	if querytime == 'day3' :
                historytime = ntime - 3600 * 24 * 3
        elif querytime == 'week1' :
                historytime = ntime - 3600 * 24 * 7
        elif querytime == 'week2' :
                historytime = ntime - 3600 * 24 * 14
    
	count_sql = 'select count(*) from cmdhistory where cmdtime > %d' % historytime	
	total = sqlinit(count_sql)[0][0]
	total_page = total/count+1
	if gotopage == -1:
		gotopage = total_page
	sql = 'select * from cmdhistory order by id desc limit %s,%s' % ((gotopage-1)*count,count)
	retstr = ''
	for onehisdata in sqlinit(sql):
        	retstr = retstr + '''<li style="list-style-type:none;"><p><span style="color:blue;">[%s]</span> 用户：<span style="color:blue;" >%s</span> 命令：<span style="color:blue;" >%s</span> 服务器：<span style="color:blue;">%s</span></p></li>''' % (time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(onehisdata[1])),onehisdata[2],onehisdata[3],onehisdata[4])
	o['li_str'] = retstr

	page_str = ''
	if gotopage > 1:
        	page_str = page_str + '''
                                <li hpagevalue="%s" data-page="%s" class="hpage">
                                    <a href="#">上一页</a></li> 
                        ''' % (querytime,gotopage-1)
	for i in range(1,total_page+1):
        	if i == gotopage:
        		page_str = page_str+'''
                                <li class="active hpage" hpagevalue="%s" data-page="%s">
                                    <a href="#">%s</a></li> 
                        ''' % (querytime,i,i)
        	else:
        		page_str = page_str+'''
                                <li hpagevalue="%s" data-page="%s" class="hpage">
                                    <a href="#">%s</a></li> 
                        ''' % (querytime,i,i)
	if gotopage < total_page:
		page_str = page_str + '''
                                <li hpagevalue="%s" data-page="%s" class="hpage">
                                    <a href="#">下一页</a></li> 
                        ''' % (querytime,gotopage+1)

	o['pagation_str'] = page_str
	return json.dumps(o)

@commandpg.route('/command/batch/')
def commandcmdbatch():
	return render_template('cmdpages/batch.html')

@commandpg.route('/command/batchcmd/')
def commandbatchcmd():
	saltqueue = Queue.Queue()	
	sername = request.args.get('serinfo')
	cmdclass = request.args.get('cmdhead')
	cmdname = request.args.get('cmdinfo').strip()

	for cmd in ['rm','mv','init','reboot','shutdown']:
		if re.findall(cmd,cmdname):
			return json.dumps("<p> <span style='color:red;font-weight:bold'>Warning</span>：您的命令：<span style='color:red;font-weight:bold'>%s</span> 被外星人劫持！详情请联系xxx</p>" % cmdname)
	if cmdclass == 'state.sls':
		status, output = commands.getstatusoutput("grep %s -r /srv/salt/cksers/|head -1|awk -F '[.]' '{print $1}'" % cmdname)
		cmdname = output.replace("/srv/salt/","").replace("/",".")
	chenkun(cmdclass,sername,cmdname,saltqueue)
	retdatas = file('saltres.txt','r')
	# 生成历史数据入库
        cmdtime = int(time.time())
	cmdshow_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        servers = sername
        cmdinfo = [cmdtime, cmdname, servers]
        if cmdclass != '' and cmdname != '' and servers != '':
                try:
                        sql = "INSERT INTO `cmdhistory` (`cmdtime`, `username`, `cmdname`, `cmdhost`) VALUES('%d', '%s', '%s', '%s')" % (cmdinfo[0], session['username'], cmdinfo[1], cmdinfo[2])
                        sqlinit(sql)
                except mysql.IntegrityError:
                        pass
	# 生成任务总数及成功失败信息
	if sername == '*':
		sername = '^'	
	else:
		sername = sername.replace('*','')
	from base.base_api import chenkun as ck 
	ser_total = ck('cmd.run','x.x.x.x','ls %s|grep %s' % (minionsdir,sername))[0]['172.16.90.14'].encode('utf-8').split('\n')
	ser_ok = saltqueue.get()
	ser_fail = [ i for i in ser_total if i not in ser_ok ]	
	if len(ser_fail) == 0:
		status_page = '''<p style="font-weight:bold; font-size:16px">[ %s ]&nbsp&nbsp&nbsp 执行总数：%s，成功：%s，失败：%s</p><p></p>''' % (cmdshow_time,len(ser_total),len(ser_ok),len(ser_fail))
		return json.dumps(status_page + retdatas.read())
	else:
		status_page = '''<p style="font-weight:bold; font-size:16px">[ %s ]&nbsp&nbsp&nbsp 执行总数：%s，成功：%s，失败：%s</p> <p style="color:#ea0000; font-weight:bold; font-size:16px">失败详情见本页最下方</p><br/>''' % (cmdshow_time,len(ser_total),len(ser_ok),len(ser_fail))
		fail_page = '''<br /> <p style="color:#ea0000; font-weight:bold; font-size:16px">执行失败的minions为：</p><p style="font-weight:bold; font-size:16px">%s</p>''' % (ser_fail)
		return json.dumps(status_page + retdatas.read() + fail_page)

@commandpg.route('/command/minionsdata/')
def commandminionsdata():
        # 获取minion的id分类
	minfo = request.args.get('mnsinfo')
	if minfo == 'mnsid':
	        res = commands.getstatusoutput("ls -l %s | awk '{print $NF}'|awk -F '[0-9]' '{print $1}'|uniq" % minionsdir)
	        clig = res[1].split('\n')
	        clig.remove('')
	        # 获取minion的id详情
	        minionslt = commands.getstatusoutput("ls -l %s | awk '{print $NF}'" % minionsdir)
	        minid = minionslt[1].split('\n')
	        minid.pop(0)

       		resstr = ''
	        for servergid in clig:
        	        resstr = resstr + '''<p style="color:#00A600;font-size:20px;"> %s* </p>''' % servergid
                	minidata = ''
	                for serminion in minid:
        	                pp = re.findall(servergid,serminion)
                	        if pp != []:
                        	        minidata = minidata + '%s &nbsp' % serminion
			resstr = resstr + '''<p>%s</p>''' % minidata
        	return resstr
	elif minfo == 'mnsgrp':
		mgroups = ['xw_web',
			]
		for mg in mgroups:
			res = commands.getstatusoutput("grep xw_web /etc/salt/master")
			return res[1]


