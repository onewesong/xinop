#!/usr/bin/env python
#coding=utf-8


import sys
reload(sys)
sys.setdefaultencoding('utf8')
sys.path.append("..")

import re, os, json, time, MySQLdb, Queue, commands, threading
from flask import Flask,request,render_template,Blueprint
from base.base_api import saltAPI, chenkun
from config.sql import sqlinit
orsyncpg = Blueprint('orsyncpg',__name__,template_folder='templates',static_folder='static')

ip_queue = Queue.Queue()
ret_queue = Queue.Queue()
confdir = '/usr/local/orsync/conf/'
retfilesdir = '/data1/netapp/orsync_tmp/'

class Mythread(threading.Thread):
        def __init__(self, ipqueue, retqueue, filesdir, modname, localmd5):
                threading.Thread.__init__(self)
                self._ipqueue = ipqueue
		self._retqueue = retqueue
		self.filesdir = filesdir
		self.modname = modname
		self.localmd5 = localmd5
        def run(self):
        	sername = self._ipqueue.get()
		# get remote server's md5
                cmdclass = 'cmd.run'
                cmdname = 'find %s -type f | xargs md5sum | sort -u > /tmp/%s_%s.txt ' % (self.filesdir, self.modname, sername)
                chenkun(cmdclass, sername, cmdname)
                # get server's md5file
                cmdclass = 'cp.push'
                cmdname = '/tmp/%s_%s.txt' % (self.modname, sername)
                chenkun(cmdclass, sername, cmdname)
		# copy md5file
		cmdclass = 'cmd.run'
                cmdname = 'cp /var/cache/salt/master/minions/%s/files/tmp/%s_%s.txt %s' % (sername, self.modname, sername, retfilesdir)
                chenkun(cmdclass, 'x.x.x.x', cmdname)

		# bijiao
		if self.localmd5 == '886f4202f9e4fea2af611f1642f84a08':
			pass
		else:
			cmd = 'cat %s%s.txt %s%s_%s.txt | sort | uniq -d > %s%s_%s_jiaoji.txt' % (retfilesdir, self.modname, retfilesdir, self.modname, sername, retfilesdir, self.modname, sername)
			os.system(cmd)
			cmdsermd5 = "md5sum %s%s_%s_jiaoji.txt | awk '{print $1}' " % (retfilesdir, self.modname, sername)
			status, servermd5 = commands.getstatusoutput(cmdsermd5)
			ret = {}
			if servermd5 == self.localmd5:
                        	md5cmd = "md5sum %s%s_%s.txt | awk '{print $1}' " % (retfilesdir, self.modname, sername)
                        	status, hostmd5 = commands.getstatusoutput(md5cmd)
				ret['retcode'] = hostmd5
				ret['server'] = sername
				self._retqueue.put(ret)
			else:
				filediff = "sort %s%s_%s_jiaoji.txt %s%s.txt | uniq -u |awk '{print $2}'|sort -n|uniq" % (retfilesdir, self.modname, sername, retfilesdir, self.modname)
				status, output = commands.getstatusoutput(filediff)
				output = output.split('\n')
				ret['retcode'] = 'error'
				ret['server'] = sername
				ret['errorfiles'] = output
				self._retqueue.put(ret)
                self._ipqueue.task_done() 

@orsyncpg.route('/orsync/md5query')
def orsyncmd5query():
	return render_template('orsyncpages/qmd5.html')

@orsyncpg.route('/orsync/upquery')
def orsyncupquery():
	return render_template('orsyncpages/qup.html')

@orsyncpg.route('/orsync/filecheck')
def orsyncfilecheck():
	starttime = time.time()
	qtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
	retinfo = {}
	modname = request.args.get('modname')
	if modname:
		modname = modname.strip()
		confile = confdir + '%s.conf' % modname
		retinfo['msg'] = ""
		if not os.path.exists(confile):
			retinfo['msg'] = ''' </br> <p style="font-weight:bold; font-size:16px; color:#F75000"> Warning : </p> <p style="font-weight:bold; font-size:16px;" > 模块 %s 不存在，请核对！</p>''' % modname
			return json.dumps(retinfo)
	else:
		retinfo['msg'] = ''' </br> <p style="font-weight:bold; font-size:16px; color:#F75000"> Warning : </p> <p style="font-weight:bold; font-size:16px;" > %s </p> ''' % '输入为空，请重新输入！'
		return json.dumps(retinfo)

	fconf = file(confile,'r')
	finfo = fconf.read()
	confinfo = eval(finfo)
	fconf.close()

	# local md5
        createlocalfile = 'find %s -type f | grep -v "\/\." | xargs md5sum | sort -u > %s%s.txt ' % (confinfo['localdir'], retfilesdir, modname)
        status, output = commands.getstatusoutput(createlocalfile)
        localmd5cmd = "md5sum %s%s.txt | awk '{print $1}' " % (retfilesdir, modname)
        status, localmd5 = commands.getstatusoutput(localmd5cmd)

	# start threading	
	ip_list = confinfo['remoteip']

	for thd in range(len(ip_list)):
		ck_thd = Mythread(ip_queue, ret_queue, confinfo['localdir'], modname, localmd5)
		ck_thd.setDaemon(True)
		ck_thd.start()
	for ip_host in ip_list:
		ip_queue.put(ip_host)
	ip_queue.join()

	# get threading's return data
	if localmd5 == '886f4202f9e4fea2af611f1642f84a08':
                info = ''
                rettime = round(float(time.time()) - float(starttime), 2)
                for ip_host in ip_list:
                        md5cmd = "md5sum %s%s_%s.txt | awk '{print $1}' " % (retfilesdir, modname, ip_host)
			status, hostmd5 = commands.getstatusoutput(md5cmd)
			info = info + ''' <p style="font-weight:bold; font-size:16px; color:blue"> %s：%s </p>''' % (ip_host, hostmd5)

		retinfo['info'] = info
		retinfo['domainname'] = '''<p style="font-size:20px;font-weight:bold"> 域名：<font size="5" face="arial" color="blue">%s</font> </p>''' % confinfo['localdir'].split('/')[3]
		retinfo['time'] = '''<p style="font-size:20px;font-weight:bold"> 查询时间：<font size="5" face="arial" color="blue">%s</font> 耗时：<font size="5" face="arial" color="blue">%s</font> <font>秒</font> </p>''' % (qtime, rettime)
		return json.dumps(retinfo)
	else:	
		okinfo = ''
		okdict = {}
		errordict = {}
		for q in range(ret_queue.qsize()):
			qret = ret_queue.get()
			if qret['retcode'] == 'error':
				errordict[qret['server']] = qret['errorfiles']
			else:
				okdict[qret['server']] = qret['retcode']
				okinfo = okinfo + ''' <p style="font-weight:bold; font-size:16px; color:blue"> %s：%s </p>''' % (qret['server'], qret['retcode'])

		errorstr = ''
		for j in errordict:
			jstr = ''' <p style="font-weight:bold; font-size:16px; color:red"> %s:%s </p> ''' % (j,errordict[j])
			errorstr = errorstr + jstr
		rettime = round(float(time.time()) - float(starttime), 2)
		retinfo['info'] = ''
		retinfo['domainname'] = '''<p style="font-size:20px;font-weight:bold"> 域名：<font size="5" face="arial" color="blue">%s</font> </p>''' % confinfo['localdir'].split('/')[3]
        	retinfo['okinfo'] = okinfo
	        retinfo['errorinfo'] = '''<p style="font-weight:bold; font-size:16px; color:red"> %s </p> ''' % str(errorstr)
		retinfo['qcount'] = '''<p style="font-size:20px;font-weight:bold"> 查询总数：%s , 同步：<font size="5" face="arial" color="blue">%s </font>, 不同步：<font size="5" face="arial" color="red">%s</font> <font> </font> </p>''' % (len(okdict.keys()) + len(errordict.keys()), len(okdict.keys()), len(errordict.keys()))
		retinfo['time'] = '''<p style="font-size:20px;font-weight:bold"> 查询时间：<font size="5" face="arial" color="blue">%s</font> 耗时：<font size="5" face="arial" color="blue">%s</font> <font>秒</font> </p>''' % (qtime, rettime)
		return json.dumps(retinfo)

@orsyncpg.route('/orsync/rsyncautoapi')
def orsyncrsyncautoapi():
        cname = request.args.get('cname')
        if cname == 'com':
		ldata = []
		for f in os.listdir(confdir):
			f = f.replace('.conf','')
			ldata.append(f)
        else:
                pass
        return json.dumps(ldata)

@orsyncpg.route('/orsync/oset')
def orsyncoset():
        return render_template("orsyncpages/oset.html",pagevalues="building ......")

@orsyncpg.route('/orsync/rycfilesquery')
def orsyncrycfilesquery():
	showinfo = request.args.get('showinfo')
        if showinfo == 'showinfo':
                sid = request.args.get('id')
                sql0 = 'select pushstatus from updatefiles where id = "%s" ' % sid
                rz = sqlinit(sql0)[0][0]
                rzidct = eval(rz.encode("utf-8"))
                retok = '推送成功：\n'
                reterror = '推送失败：\n'
                for i in rzidct:
                        if rzidct[i] == 'ok':
                                retok = retok + i + '\n'
                        else:
                                reterror = reterror + i + '\n'
                ret = retok + reterror
                return ret
        modname = request.args.get('modname').encode("utf-8")
        if modname == '':
                modname = '0'
        dateinfo = request.args.get('dateinfo').encode("utf-8")
        qtime = int(time.time())
	querytime = time.strftime("%H:%M:%S", time.localtime(qtime))
        if dateinfo == '一天内' :
                querydate = qtime - 3600*24
        elif dateinfo == '三天内' :
                querydate = qtime - 3600*72
        elif dateinfo == '本周内' :
                querydate = qtime - 3600*168

        def sqlset(modname):
                if modname == '0' :
                        sql0 = 'select * from updatefiles where time > %s order by time desc' % querydate

                else:
                        sql0 = 'select * from updatefiles where modname = "%s" and time > %s order by time desc' % (modname, querydate)
                return sql0
        o = {
        'status':1,
        'table_str':'',
        'total_page':'',
        'pagation_str':'',
        'rzcount':''
        }

        init_str = ''
        sql0 = sqlset(modname)
        try:
                sqlrz = sqlinit(sql0)
        except Exception,e:
                sqlrz = sqlinit(sql0)

        rzcount = len(sqlrz)
        for c in sqlrz:
                try:
                        frz = eval(c[3].encode("utf-8"))
                except Exception,e:
                        frz = {'Null':'Null'}
                frzstatus = frz.values()
                fok = frzstatus.count('ok')
                ferror = frzstatus.count('error')
                if ferror > 0 :
                        ferror = '<font color="red" size="5"> %s </font>' % ferror
                fallsize = len(frzstatus)
                fret = '更新服务器数：%s，成功：%s，失败：%s' % (fallsize, fok, ferror)
                ftime = c[2]
                ltime = time.localtime(int(ftime))
                timeStr = time.strftime("%Y-%m-%d %H:%M:%S", ltime)
                #init_str = init_str + '''<tr><td> %s</td><td>%s</td><td>%s&nbsp&nbsp <button data-id="%s" class="btn btn-info showxq">详情</button></td><td>%s</td><td>%s</td>''' % (timeStr, c[1], fret, c[0], c[4], c[5])
                init_str = init_str + '''<tr><td> %s</td><td>%s</td><td>%s&nbsp&nbsp <button data-id="%s" class="btn btn-info showxq">详情</button></td><td><font color="blue" size="4"> %s </font></td><td>%s</td>''' % (timeStr, c[1], fret, c[0], c[4], c[5])
        o['table_str'] = init_str
	o['rzcount'] = '''<p style="font-size:20px;font-weight:bold"> &nbsp&nbsp 上线次数：<font size="5" face="arial" color="blue">%s</font> &nbsp&nbsp 当前时间：<font size="5" face="arial" color="blue">%s</font> </p>''' % (rzcount, querytime)
        return json.dumps(o)

@orsyncpg.route('/orsync/autoconfig')
def orsyncautoconfig():
        inputmodname = request.args.get('modname').strip()
        dirname = request.args.get('dirname').strip()
        hostsip = request.args.get('hostsip').strip()
###
        codedir = '/data1/webapps/'
        o = {
                'modstatus':'',
                }

# 检测输入是否为空
        if inputmodname == '' or dirname == '' or hostsip == '':
                o['modstatus'] = '<p style="color:red;font-weight:bold">输入不能为空！</p>'
                return json.dumps(o)
###
	conf_dir = '/usr/local/orsync/conf/'
	base_config = 'base.config'

# 检测用户输入的模块是否已存在
        for conffile in os.listdir(conf_dir):
                if re.findall('conf$', conffile):
                        fr = open(conf_dir + conffile)
                        frz = fr.read()
                        rz = eval(frz.replace('\n',''))
                        fmodname = rz['modname']
                        if inputmodname == fmodname:
                                o['modstatus'] = '<p style="font-weight:bold">Warning：模块 <font style="color:red;font-weight:bold"> %s </font>已存在！</p>' % inputmodname
                                return json.dumps(o)
# 创建代码目录
        if not os.path.isdir(codedir + dirname):
                os.makedirs(codedir + dirname)
        else:
                o['modstatus'] = '<p>Warning：目录 <font style="color:red;font-weight:bold"> %s </font>已存在！</p>' % dirname
                return json.dumps(o)
# 读取base.config
        frbase = open(conf_dir + base_config)
        frzbase = frbase.read()
        rzbase = eval(frz.replace('\n',''))

# 检测前端机
        host_ok = ''
        host_error = ''
        cktag = ''
        sers = []
        for server_ip in hostsip.split():
                sers.append(server_ip.encode("utf-8"))
                rsync_cmd = "rsync -avzrP --exclude-from=%s %s/ %s@%s::%s/" % ('/usr/local/orsync/conf/exclude.list', codedir + dirname, rzbase['rsync_user'], server_ip, inputmodname)
                print 'rsync_cmd: ', rsync_cmd
                status, localoutput = commands.getstatusoutput(rsync_cmd)
                if status == 0: #推送成功
                        host_ok = host_ok + '<p>前端机：%s <font style="color:blue;font-weight:bold"> 设置成功！</font></p>' % server_ip
                else:
                        cktag = 'error'
                        host_error = host_error + '<div class="box"><p>前端机：%s <font style="color:red;font-weight:bold"> 检测失败！ %s </font></p></div>' % (server_ip, localoutput)

# 配置及启动 orsync 模块
        if cktag == '':
                f = file('/usr/local/orsync/conf/base.config')
                fr = f.read()
                fr = fr.replace('"modname":""', '"modname":"%s"' % inputmodname)
                fr = fr.replace('"localdir":""', '"localdir":"%s"' % (codedir + dirname))
                fr = fr.replace("[\n]", str(sers))
                # 
                fw = file(conf_dir + inputmodname + '.conf','w')
                fw.write(fr)
                fw.close()
                f.close()
                os.system('nohup /usr/local/orsync/projects/orsync.py /usr/local/orsync/conf/%s.conf &' % inputmodname)
        elif cktag == 'error':
                os.rmdir(codedir + dirname)

        #o['modstatus'] = '%s ok' % inputmodname
        o['host_ok'] = host_ok
        o['host_error'] = host_error
        return json.dumps(o)


