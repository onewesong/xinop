#!/usr/bin/env python
#coding=utf-8

import re, os, xlrd, xlwt, time, json, Queue, urllib2
import MySQLdb as mysql

import sys
reload(sys)
sys.setdefaultencoding('utf8')
sys.path.append("..")
from config.sql import sqlinit

from flask import Flask,request,redirect,render_template,Blueprint,send_from_directory
cmdbpg = Blueprint('bpt2',__name__,template_folder='templates',static_folder='static')

idc_queue = Queue.Queue()
rack_queue = Queue.Queue()
nd_queue = Queue.Queue()
vm_queue = Queue.Queue()
sou_queue = Queue.Queue()

fn_path=os.path.join(os.getcwd(),'files/')
UPLOAD_FOLDER = 'files/'

def testXlwt(file_read):
        book_read = xlrd.open_workbook(file_read)       #读excel表
        sh = book_read.sheet_by_index(0)        #获取其sheet1
        nrows = sh.nrows        #sheet1的行数
        ncols = sh.ncols        #sheet1的列数

	o = {}
	warning, info = '', ''
        for i in range(1,nrows):
                row_data = sh.row_values(i)     #第i行的值
		hdata = []
		errortag = 0
                for hostitem in row_data:
			if type(hostitem) == float:
				hdata.append(int(hostitem))
			else:
				hdata.append(hostitem)
		hrack, hsite, devstyle, usize, cpunum, memnum, memsize, disk, disksize, diskgt, raid, insidecard, insideip, insidesw, iport, ivlan, outsidecard, outsideip, outsidesw, oport, ovlan, mngcard, mngip, mngsw, mngport, mngvlan, devicetype, osversion, busstyle, codeenv, assetnumber, owner, runstatus, remarks = tuple(hdata)
		for dvport in [(insidesw, iport), (outsidesw, oport), (mngsw, mngport)]:
                	sql0 = 'select ndname from ndports where ndname = "%s" and ndport = "%s"' % dvport
                	rz = sqlinit(sql0)
                	if rz != ():	# 交换机存在
                        	if rz[0][0] != '':	#且该端口被占用
                        		warning = warning + ''' <p> %s添加失败！交换机（%s）：端口（%s）已存在</p> ''' % (insideip, dvport[0], dvport[1])
					errortag = 1
                	else:
				pass
		if errortag == 1:
			continue
		sql = 'insert into hosts (hrack, hsite, devstyle, usize, cpunum, memnum, memsize, disk, disksize, diskgt, raid, insidecard, insideip, insidesw, iport, ivlan, outsidecard, outsideip, outsidesw, oport, ovlan, mngcard, mngip, mngsw, mngport, mngvlan, devicetype, osversion, busstyle, codeenv, assetnumber, owner, runstatus, remarks, sitecode) values ("%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s")' % (hrack, hsite, devstyle, usize, cpunum, memnum, memsize, disk, disksize, diskgt, raid, insidecard, insideip, insidesw, iport, ivlan, outsidecard, outsideip, outsidesw, oport, ovlan, mngcard, mngip, mngsw, mngport, mngvlan, devicetype, osversion, busstyle, codeenv, assetnumber, owner, runstatus, remarks, hsite.split('-')[0])
                sqlndport1 = 'INSERT INTO `ndports` (`ndname`, `ndport`, `ndvlan`, `ndlinknd`, `linkndport`, `linkndipaddr`) VALUES ("%s", "%s", "%s", "%s", "%s", "%s")' % (insidesw, iport, ivlan, assetnumber, insidecard, insideip)
                sqlndport2 = 'INSERT INTO `ndports` (`ndname`, `ndport`, `ndvlan`, `ndlinknd`, `linkndport`, `linkndipaddr`) VALUES ("%s", "%s", "%s", "%s", "%s", "%s")' % (outsidesw, oport, ovlan, assetnumber, outsidecard, outsideip)
                sqlndport3 = 'INSERT INTO `ndports` (`ndname`, `ndport`, `ndvlan`, `ndlinknd`, `linkndport`, `linkndipaddr`) VALUES ("%s", "%s", "%s", "%s", "%s", "%s")' % (mngsw, mngport, mngvlan, assetnumber, mngcard, mngip)
                try:
                        sqlinit(sql)
                        if insidesw and iport and ivlan and insidecard and insideip:
                                sqlinit(sqlndport1)
                        if outsidesw and oport and ovlan and outsidecard and outsideip:
                                sqlinit(sqlndport2)
                        if mngsw and mngport and mngvlan and mngcard and mngip:
                                sqlinit(sqlndport3)
                        info = info + '<p> %s 添加成功！</p>' % insideip
                except:
                        pass
		#rz = rz + 'ok'
	o['warning'] = warning
	o['info'] = info
	return o

rackhostsqueryformat = ''' 
<tr>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>%s*%sGB</td>
<td>%s*%s%s / %s</td>
<td>%s / %s /<a style="font-size:15px;font-weight:bold" href="/cmdb/netdevice/%s"> %s </a>/ %s / %s </td>
<td>%s / %s /<a style="font-size:15px;font-weight:bold" href="/cmdb/netdevice/%s"> %s </a>/ %s / %s </td>
<td>%s / %s /<a style="font-size:15px;font-weight:bold" href="/cmdb/netdevice/%s"> %s </a>/ %s / %s </td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>
<button data-id="%s" rack-name="%s" objecttype="%s" class="btn btn-warning phydlt">删除</button>&nbsp
<button data-id="%s" rack-name="%s" objecttype="%s" class="btn btn-info phyupdate">修改</button>
</td>
</tr>
'''
hostsqueryformat = ''' 
<tr>
<td><a style="font-size:15px;font-weight:bold" href="/cmdb/rackhosts/%s">%s</a> / %s</td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>%s*%sGB</td>
<td>%s*%s%s / %s</td>
<td>%s / %s /<a style="font-size:15px;font-weight:bold" href="/cmdb/netdevice/%s"> %s </a>/ %s / %s </td>
<td>%s / %s /<a style="font-size:15px;font-weight:bold" href="/cmdb/netdevice/%s"> %s </a>/ %s / %s </td>
<td>%s / %s /<a style="font-size:15px;font-weight:bold" href="/cmdb/netdevice/%s"> %s </a>/ %s / %s </td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>
<button data-id="%s" rack-name="%s" objecttype="%s" class="btn btn-warning phydlt">删除</button>&nbsp
<button data-id="%s" rack-name="%s" objecttype="%s" class="btn btn-info phyupdate">修改</button>
</td>
</tr>
'''

racknetdevicesqueryformat = ''' 
<tr>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>
<button data-id="%s" rack-name="%s" objecttype="%s" class="btn btn-warning nddlt">删除</button>&nbsp
<button data-id="%s" rack-name="%s" objecttype="%s" class="btn btn-info ndupdate">修改</button>
</td>
</tr> 
'''
netdevicesqueryformat = ''' 
<tr>
<td>%s / %s</td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>
<button data-id="%s" rack-name="%s" objecttype="%s" class="btn btn-warning nddlt">删除</button>&nbsp
<button data-id="%s" rack-name="%s" objecttype="%s" class="btn btn-info ndupdate">修改</button>
</td>
</tr> 
'''


############################# page #####################

@cmdbpg.route('/')
def hidx():
	#return render_template('cmdbpg/cmdb.html')
	return render_template('cmdbpg/index.html')

@cmdbpg.route('/cmdb/idc')
def cmdbidc():
	return render_template('cmdbpg/idc.html')

@cmdbpg.route('/cmdb/idcform')
def cmdbidcadd():
	return render_template('cmdbpg/idcform.html')

@cmdbpg.route('/cmdb/hostform')
def cmdbhostadd():
	return render_template('cmdbpg/hostform.html')

@cmdbpg.route('/cmdb/hosts')
def cmdbhosts():
	return render_template('cmdbpg/hostsindex.html')

@cmdbpg.route('/cmdb/count', methods=['GET','POST'])
def cmdbcount():
        if request.method=='POST':
                try:
                        file_name = request.files['fn']
			if not file_name:
				ret = {}
				ret['error'] = '上传为空...'
				return json.dumps(ret)
                        file_name.save(os.path.join(fn_path, file_name.filename))
			filepath = fn_path + file_name.filename
			ret = testXlwt(filepath)
			ret['error'] = 0
                        return json.dumps(ret)
                except IOError:
                        return '上传为空...'
        else:
                return render_template('cmdbpg/count.html')

@cmdbpg.route('/cmdb/history')
def cmdbhistory():
	return render_template('cmdbpg/history.html', hvalues = "building ......")

@cmdbpg.route('/cmdb/vmhosts')
def cmdbvmhosts():
        return render_template("cmdbpg/vmhosts.html")

@cmdbpg.route('/cmdb/phymachines')
def cmdbphymachine():
        return render_template("cmdbpg/phymachines.html")

@cmdbpg.route('/cmdb/netdevices')
def cmdbnetdevices():
        return render_template("cmdbpg/netdevicesall.html")

@cmdbpg.route('/cmdb/netdevice/<ndname>')
def cmdbnetdevice(ndname):
        nd_queue.put(ndname)
        return render_template("cmdbpg/netdevice.html",ndname = ndname)

@cmdbpg.route('/cmdb/vms/<ip_env>')
def cmdbvms(ip_env):
        vmhostip = ip_env.split('_')[0]
        vm_queue.put(ip_env)
        return render_template("cmdbpg/vms.html",vmhostip = vmhostip)

@cmdbpg.route('/cmdb/rackhosts/<rackname>')
def cmdbrackhosts(rackname):
        rack_queue.put(rackname)
	#return 'ok'
        return render_template("cmdbpg/rack_hosts.html",rackname = rackname)

@cmdbpg.route('/cmdb/idcracks/<idcname>')
def queryidcid(idcname):
        idc_queue.put(idcname)
        return render_template("cmdbpg/idc_rack.html",idcname = idcname)

############################## api ##############################

@cmdbpg.route('/cmdb/delete')
def cmdbdelete():
	cmdbtype = request.args.get('cmdbtype')
        delete_id = request.args.get('id')
	if cmdbtype == 'idc':
		sql = 'delete from idcs where id = %s' % (delete_id)
		sqlinit(sql)
		return 'ok'
	elif cmdbtype == 'rack':
        	delete_id = request.args.get('id')
        	sqlidcname = 'select idcname from racks where id = "%s" ' % (delete_id)
        	idcname = sqlinit(sqlidcname)[0][0]
        	sqldlt = 'delete from racks where id = %s' % (delete_id)
        	sqlinit(sqldlt)
        	return redirect('/cmdb/idcracks/%s' % idcname)
	elif cmdbtype == 'phymachine':
		rackname = request.args.get('rackname')
		# delete ports
		netinfosql = 'select insideip, insidesw, outsideip, outsidesw, mngip, mngsw from hosts where id = "%s" ' % delete_id 
		netdata = sqlinit(netinfosql)
		insideip, insidesw, outsideip, outsidesw, mngip, mngsw = netdata[0][0], netdata[0][1], netdata[0][2], netdata[0][3], netdata[0][4], netdata[0][5]
		sqldel1 = 'delete from ndports where ndname = "%s" and linkndipaddr = "%s" ' % (insidesw, insideip)
		sqldel2 = 'delete from ndports where ndname = "%s" and linkndipaddr = "%s" ' % (outsidesw, outsideip)
		sqldel3 = 'delete from ndports where ndname = "%s" and linkndipaddr = "%s" ' % (mngsw, mngip)
		sqlinit(sqldel1)
		sqlinit(sqldel2)
		sqlinit(sqldel3)
		# delete host itself
		sql = 'delete from hosts where id = %s' % (delete_id)
		sqlinit(sql)
		# redirect page
		return redirect('/cmdb/rackhosts/%s' % rackname)
        elif cmdbtype == 'phymachinesall':
                # delete ports
                netinfosql = 'select insideip, insidesw, outsideip, outsidesw, mngip, mngsw from hosts where id = "%s" ' % delete_id
                netdata = sqlinit(netinfosql)
                insideip, insidesw, outsideip, outsidesw, mngip, mngsw = netdata[0][0], netdata[0][1], netdata[0][2], netdata[0][3], netdata[0][4], netdata[0][5]
                sqldel1 = 'delete from ndports where ndname = "%s" and linkndipaddr = "%s" ' % (insidesw, insideip)
                sqldel2 = 'delete from ndports where ndname = "%s" and linkndipaddr = "%s" ' % (outsidesw, outsideip)
                sqldel3 = 'delete from ndports where ndname = "%s" and linkndipaddr = "%s" ' % (mngsw, mngip)
                sqlinit(sqldel1)
                sqlinit(sqldel2)
                sqlinit(sqldel3)
                # delete host itself
                sql = 'delete from hosts where id = %s' % (delete_id)
                sqlinit(sql)
                return 'ok'
	elif cmdbtype == 'netdevice':
                rackname = request.args.get('rackname')
		sqlndname = 'select ndname from netdevices where id = %s' % (delete_id)
		ndname = sqlinit(sqlndname)[0][0]
		# update link server's port
		sqllinknd = 'select ndlinknd from ndports where ndname = "%s" ' % (ndname)
		for linknd in sqlinit(sqllinknd):
                        sql = 'select * from hosts where assetnumber = "%s"' % linknd[0]
                        rz = sqlinit(sql)
                        if rz == ():
                                continue
                        rz = rz[0]
                        ndindex = rz.index(ndname)
                        if ndindex == 15:
                                sw, port = 'insidesw', 'iport'
                        if ndindex == 20:
                                sw, port = 'outsidesw', 'oport'
                        if ndindex == 25:
                                sw, port = 'mngsw', 'mngport'
                        sql = 'update hosts set %s = "", %s = "" where assetnumber = "%s"' % (sw, port, linknd[0])
                        sqlinit(sql)
		# delete netdevices's port 
		delndports = 'delete from ndports where ndname = "%s" or ndlinknd = "%s" ' % (ndname, ndname)
		sqlinit(delndports)
		# delete netdevice
		sql = 'delete from netdevices where id = %s' % (delete_id)
		sqlinit(sql)
		# redirect page
		return redirect('/cmdb/rackhosts/%s' % rackname)
	elif cmdbtype == 'netdevicesall':
                sqlndname = 'select ndname from netdevices where id = %s' % (delete_id)
                ndname = sqlinit(sqlndname)[0][0]
                # update link server's port
                sqllinknd = 'select ndlinknd from ndports where ndname = "%s" ' % (ndname)
                for linknd in sqlinit(sqllinknd):
                        sql = 'select * from hosts where assetnumber = "%s"' % linknd[0]
                        rz = sqlinit(sql)
			if rz == ():
				continue
			rz = rz[0]
                        ndindex = rz.index(ndname)
                        if ndindex == 15:
                                sw, port = 'insidesw', 'iport'
                        if ndindex == 20:
                                sw, port = 'outsidesw', 'oport'
                        if ndindex == 25:
                                sw, port = 'mngsw', 'mngport'
                        sql = 'update hosts set %s = "", %s = "" where assetnumber = "%s"' % (sw, port, linknd[0])
                        sqlinit(sql)
                # delete netdevices's port 
                delndports = 'delete from ndports where ndname = "%s" or ndlinknd = "%s" ' % (ndname, ndname)
                sqlinit(delndports)
                # delete netdevice
                sql = 'delete from netdevices where id = %s' % (delete_id)
                sqlinit(sql)
		return 'ok'
        elif cmdbtype == 'ndport':
		delete_id = request.args.get('id')
		ndname = request.args.get('ndname')
		# delete hosts ndport
		sqllinknd = 'select ndlinknd from ndports where id = "%s" ' % (delete_id)
		linknd = sqlinit(sqllinknd)
                sql = 'select * from hosts where assetnumber = "%s"' % linknd[0]
                rz = sqlinit(sql)
                if rz == ():
      	        	return 'ndlinknd null ...'
                rz = rz[0]
                ndindex = rz.index(ndname)
                if ndindex == 15:
               		sw, port = 'insidesw', 'iport'
                if ndindex == 20:
                	sw, port = 'outsidesw', 'oport'
                if ndindex == 25:
                	sw, port = 'mngsw', 'mngport'
                sql = 'update hosts set %s = "", %s = "" where assetnumber = "%s"' % (sw, port, linknd[0][0])
                sqlinit(sql)
		# delete ndports
		sql = 'delete from ndports where id = %s' % (delete_id)
		sqlinit(sql)
		return redirect('/cmdb/netdevice/%s' % ndname)
        elif cmdbtype == 'vmhost':
                delete_id = request.args.get('id')
                netinfosql = 'select insideip, insidesw from hosts where id = "%s" ' % delete_id
                netdata = sqlinit(netinfosql)
                hostip, hostsw = netdata[0][0], netdata[0][1]
                sqldltsw = 'delete from ndports where ndname = "%s" and linkndipaddr = "%s" ' % (hostsw, hostip)
                sqlinit(sqldltsw)
                sql = 'delete from hosts where id = %s' % (delete_id)
                sqlinit(sql)
                return 'ok'
	elif cmdbtype == 'vms':
		delete_id = request.args.get('id')
		vmhostinfo = request.args.get('vmhostinfo')
		sql = 'delete from vms where id = %s' % (delete_id)
		sqlinit(sql)
		return redirect('/cmdb/vms/%s' % vmhostinfo)

@cmdbpg.route('/cmdb/update')
def cmdbupdate():
        cmdbtype = request.args.get('cmdbtype')
	if cmdbtype == 'idc':
		idcid = request.args.get('id')
		idcname = request.args.get('idcname').encode("utf-8")
        	if idcname:
            		sql = 'update idcs set idcname = "%s" where id = %s' % (idcname.strip(),idcid)
        		sqlinit(sql)
        	idcaddr = request.args.get('idcaddr').encode("utf-8")
        	if idcaddr:
            		sql = 'update idcs set idcaddr = "%s" where id = %s' % (idcaddr.strip(),idcid)
        		sqlinit(sql)
        	idccontacts = request.args.get('idccontacts').encode("utf-8")
        	if idccontacts:
            		sql = 'update idcs set idccontacts = "%s" where id = %s' % (idccontacts.strip(),idcid)
        		sqlinit(sql)
        	ctnumber = request.args.get('ctnumber').encode("utf-8")
        	if ctnumber:
            		sql = 'update idcs set idcphone = "%s" where id = %s' % (ctnumber.strip(),idcid)
        		sqlinit(sql)
        	idcnote = request.args.get('idcnote').encode("utf-8")
        	if idcnote:
            		sql = 'update idcs set idcnote = "%s" where id = %s' % (idcnote.strip(),idcid)
        		sqlinit(sql)
		return 'ok'
	if cmdbtype == 'rack':
		rackid = request.args.get('id')
		rackname = request.args.get('rackname').encode("utf-8")
		if rackname:
			sql = 'update racks set rackname = "%s" where id = %s' % (rackname.strip(),rackid)
			sqlinit(sql)
		rackaddr = request.args.get('rackaddr').encode("utf-8")
		if rackaddr:
			sql = 'update racks set rackaddr = "%s" where id = %s' % (rackaddr.strip(),rackid)
			sqlinit(sql)
		racksize = request.args.get('racksize').encode("utf-8")
		if racksize:
			sql = 'update racks set racksize = "%s" where id = %s' % (racksize.strip(),rackid)
			sqlinit(sql)
		racknote = request.args.get('racknote').encode("utf-8")
		if racknote:
			sql = 'update racks set racknote = "%s" where id = %s' % (racknote.strip(),rackid)
			sqlinit(sql)
		# redirect
        	sqlidcname = 'select idcname from racks where id = "%s" ' % rackid
        	idcname = sqlinit(sqlidcname)[0][0]
        	return redirect('/cmdb/idcracks/%s' % idcname)
	if cmdbtype == 'host' or cmdbtype == 'phymachine' or cmdbtype == 'vmhost' :
		hostid = request.args.get('id')
		hrack = request.args.get('hrack').encode("utf-8")
		if hrack:
			sql = 'update hosts set hrack = "%s" where id = %s ' % (hrack.strip(),hostid)
			sqlinit(sql)
		hsite = request.args.get('hsite').encode("utf-8")
		if hsite:
			sql = 'update hosts set hsite = "%s" where id = %s ' % (hsite.strip(),hostid)
			sqlinit(sql)
		sertype = request.args.get('sertype').encode("utf-8")
		if sertype:
			sql = 'update hosts set sertype = "%s" where id = %s ' % (sertype.strip(),hostid)
			sqlinit(sql)
		busstyle = request.args.get('busstyle').encode("utf-8")
		if busstyle:
			sql = 'update hosts set busstyle = "%s" where id = %s ' % (busstyle.strip(),hostid)
			sqlinit(sql)
		codeenv = request.args.get('codeenv').encode("utf-8")
		if codeenv:
			sql = 'update hosts set codeenv = "%s" where id = %s ' % (codeenv.strip(),hostid)
			sqlinit(sql)
		hostnote = request.args.get('hostnote').encode("utf-8")
		if hostnote:
			sql = 'update hosts set remarks = "%s" where id = %s ' % (hostnote.strip(),hostid)
			sqlinit(sql)
		if cmdbtype == 'host' :
			sqlrackname = 'select hrack from hosts where id = "%s" ' % hostid
			rackname = sqlinit(sqlrackname)[0][0]
			return redirect('/cmdb/rackhosts/%s' % rackname)
		elif cmdbtype == 'phymachine' :	
			return 'ok'
		elif cmdbtype == 'vmhost' :
			return 'ok'
	if cmdbtype == 'netdevice' or cmdbtype == 'netdevicesall' :
		ndid = request.args.get('id')
		ndrack = request.args.get('ndrack').encode("utf-8")
		if ndrack :
			sql = 'update netdevices set ndrack = "%s" where id = %s ' % (ndrack.strip(),ndid)
			sqlinit(sql)
		ndaddr = request.args.get('ndaddr').encode("utf-8")
		if ndaddr :
			sql = 'update netdevices set ndaddr = "%s" where id = %s ' % (ndaddr.strip(),ndid)
			sqlinit(sql)
		ndnote = request.args.get('ndnote').encode("utf-8")
		if ndnote :
			sql = 'update netdevices set ndnote = "%s" where id = %s ' % (ndnote.strip(),ndid)
			sqlinit(sql)
		if cmdbtype == 'netdevice' :
			sqlrackname = 'select ndrack from netdevices where id = "%s" ' % ndid
			rackname = sqlinit(sqlrackname)[0][0]
			return redirect('/cmdb/rackhosts/%s' % rackname)
		if cmdbtype == 'netdevicesall' :
			return 'ok'
	if cmdbtype == 'vms' :
		vmid = request.args.get('id')
		ip_env = request.args.get('ip_env')
		serstyle = request.args.get('serstyle').encode("utf-8")
		if serstyle :
			sql = 'update vms set serstyle = "%s" where id = %s ' % (serstyle.strip(),vmid)
			sqlinit(sql)
		busstyle = request.args.get('busstyle').encode("utf-8")
		if busstyle :
			sql = 'update vms set busstyle = "%s" where id = %s ' % (busstyle.strip(),vmid)
			sqlinit(sql)
		remarks = request.args.get('remarks').encode("utf-8")
		if remarks :
			sql = 'update vms set remarks = "%s" where id = %s ' % (remarks.strip(),vmid)
			sqlinit(sql)
		return redirect('/cmdb/vms/%s' % ip_env)

@cmdbpg.route('/cmdb/add')
def cmdbadd():
        cmdbtype = request.args.get('cmdbtype')
	if cmdbtype == 'idc':
                o = {}
                o['status'] = 1
                idcname = request.args.get('idcname').encode("utf-8")
                idcaddr = request.args.get('idcaddr').encode("utf-8")
                idccontacts = request.args.get('idccontacts').encode("utf-8")
                idcphone = request.args.get('idcphone').encode("utf-8")
                idcnote = request.args.get('idcnote').encode("utf-8")
                sql = 'insert into idcs (idcname, idcaddr, idccontacts, idcphone, idcnote) values ("%s","%s","%s","%s","%s")' % (idcname.strip(), idcaddr.strip(), idccontacts.strip(), idcphone.strip(), idcnote.strip())
                try:
                        sqlinit(sql)
                        o['status'] = 0
                        o['info'] = '<p><span style="color:blue;font-weight:bold"> %s 添加成功！</span></p>' % idcname
                except:
                        pass
                return json.dumps(o)
	elif cmdbtype == 'rack':
                o = {}
                o['status'] = 1
                rackname = request.args.get('rackname').encode("utf-8")
                rackidc = request.args.get('rackidc').encode("utf-8")
                rackaddr = request.args.get('rackaddr').encode("utf-8")
                racksize = request.args.get('racksize').encode("utf-8")
                racknote = request.args.get('racknote').encode("utf-8")
                sql = 'insert into racks (rackname, idcname, rackaddr, racksize, racknote) values ("%s","%s","%s","%s","%s")' % (rackname.strip(), rackidc.strip(), rackaddr.strip(), racksize.strip(), racknote.strip())
                try:
                        sqlinit(sql)
                        o['status'] = 0
                        o['info'] = '<p><span style="color:blue;font-weight:bold"> %s 添加成功！</span></p>' % rackname
                except:
                        pass
                return json.dumps(o)
	elif cmdbtype == 'host':
        	o = {}
        	o['status'] = 1
        	devstyle = request.args.get('devstyle').encode("utf-8")
        	cpunum = request.args.get('cpunum').encode("utf-8")
        	memnum = request.args.get('memnum').encode("utf-8")
        	memsize = request.args.get('memsize').encode("utf-8")
        	disk = request.args.get('disk').encode("utf-8")
        	disksize = request.args.get('disksize').encode("utf-8")
        	raid = request.args.get('raid').encode("utf-8")
        	diskgt = request.args.get('diskgt').encode("utf-8")
        	insidecard = request.args.get('insidecard').encode("utf-8")
        	insideip = request.args.get('insideip').encode("utf-8")
        	insidesw = request.args.get('insidesw').encode("utf-8")
        	iport = request.args.get('iport').encode("utf-8")
        	ivlan = request.args.get('ivlan').encode("utf-8")
        	outsidecard = request.args.get('outsidecard').encode("utf-8")
        	outsideip = request.args.get('outsideip').encode("utf-8")
        	outsidesw = request.args.get('outsidesw').encode("utf-8")
                oport = request.args.get('oport').encode("utf-8")
        	ovlan = request.args.get('ovlan').encode("utf-8")
        	mngcard = request.args.get('mngcard').encode("utf-8")
        	mngip = request.args.get('mngip').encode("utf-8")
        	mngsw = request.args.get('mngsw').encode("utf-8")
                mngport = request.args.get('mngport').encode("utf-8")
        	mngvlan = request.args.get('mngvlan').encode("utf-8")
        	hrack = request.args.get('hrack').encode("utf-8")
        	hsite = request.args.get('hsite').encode("utf-8")
        	osversion = request.args.get('osversion').encode("utf-8")
        	busstyle = request.args.get('busstyle').encode("utf-8")
        	codeenv = request.args.get('codeenv').encode("utf-8")
        	assetnumber = request.args.get('assetnumber').encode("utf-8")
        	remarks = request.args.get('remarks').encode("utf-8")
        	devicetype = request.args.get('devicetype').encode("utf-8")
		owner = request.args.get('owner').encode("utf-8")
		runstatus = request.args.get('runstatus').encode("utf-8")
		usize = request.args.get('usize').encode("utf-8")
        	# check sw and port
		for dvport in [(insidesw, iport), (outsidesw, oport), (mngsw, mngport)]:
        		sql0 = 'select ndname from ndports where ndname = "%s" and ndport = "%s"' % dvport
        		#rz = str(sqlinit(sql0)[0][0])
        		rz = sqlinit(sql0)
        		if rz != ():
        			#o['info'] = '交换机 %s 端口 %s 已存在' % dvport
				if rz[0][0] != '':
        				o['info'] = ''' <p style="font-size:23px;font-weight:bold"> 交换机（%s）<font size="5" face="arial" color="blue">端口 %s</font> 已存在</p> ''' % dvport
        				return json.dumps(o)
			else:
        	sql = 'insert into hosts (hrack, hsite, devstyle, usize, cpunum, memnum, memsize, disk, disksize, diskgt, raid, insidecard, insideip, insidesw, iport, ivlan, outsidecard, outsideip, outsidesw, oport, ovlan, mngcard, mngip, mngsw, mngport, mngvlan, devicetype, osversion, busstyle, codeenv, assetnumber, owner, runstatus, remarks, sitecode) values ("%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s")' % (hrack.strip(), hsite.strip(), devstyle.strip(), usize.strip(), cpunum.strip(), memnum.strip(), memsize.strip(), disk.strip(), disksize.strip(), diskgt, raid, insidecard.strip(), insideip.strip(), insidesw.strip(), iport.strip(), ivlan.strip(), outsidecard.strip(), outsideip.strip(), outsidesw.strip(), oport.strip(), ovlan.strip(), mngcard.strip(), mngip.strip(), mngsw.strip(), mngport.strip(), mngvlan.strip(), devicetype.strip(), osversion.strip(), busstyle.strip(), codeenv, assetnumber.strip(), owner.strip(), runstatus.strip(), remarks.strip(), hsite.strip().split('-')[0])
        	sqlndport1 = 'INSERT INTO `ndports` (`ndname`, `ndport`, `ndvlan`, `ndlinknd`, `linkndport`, `linkndipaddr`) VALUES ("%s", "%s", "%s", "%s", "%s", "%s")' % (insidesw.strip(), iport.strip(), ivlan.strip(), assetnumber.strip(), insidecard.strip(), insideip.strip())
        	sqlndport2 = 'INSERT INTO `ndports` (`ndname`, `ndport`, `ndvlan`, `ndlinknd`, `linkndport`, `linkndipaddr`) VALUES ("%s", "%s", "%s", "%s", "%s", "%s")' % (outsidesw.strip(), oport.strip(), ovlan.strip(), assetnumber.strip(), outsidecard.strip(), outsideip.strip())
        	sqlndport3 = 'INSERT INTO `ndports` (`ndname`, `ndport`, `ndvlan`, `ndlinknd`, `linkndport`, `linkndipaddr`) VALUES ("%s", "%s", "%s", "%s", "%s", "%s")' % (mngsw.strip(), mngport.strip(), mngvlan.strip(), assetnumber.strip(), mngcard.strip(), mngip.strip())
        	try:
                	sqlinit(sql)
			if insidesw and iport and ivlan and insidecard and insideip:
        			sqlinit(sqlndport1)
			if outsidesw and oport and ovlan and outsidecard and outsideip:
        			sqlinit(sqlndport2)
			if mngsw and mngport and mngvlan and mngcard and mngip:
        			sqlinit(sqlndport3)
                	o['status'] = 0
        		o['info'] = '<p><span style="color:blue;font-weight:bold"> %s 添加成功！</span></p>' % assetnumber
        	except:
                	pass
        	return json.dumps(o)
	elif cmdbtype == 'vms':
        	o = {}
        	devicetype = request.args.get('devicetype').encode("utf-8")
        	vmhostip = request.args.get('vmhostip').encode("utf-8")
        	serstyle = request.args.get('serstyle').encode("utf-8")
        	busstyle = request.args.get('busstyle').encode("utf-8")
        	cpunum = request.args.get('cpunum').encode("utf-8")
        	memsize = request.args.get('memsize').encode("utf-8")
        	disk = request.args.get('disk').encode("utf-8")
        	disksize = request.args.get('disksize').encode("utf-8")
        	diskgt = request.args.get('diskgt').encode("utf-8")
        	insidecard = request.args.get('insidecard').encode("utf-8")
        	insideip = request.args.get('insideip').encode("utf-8")
        	codeenv = request.args.get('codeenv').encode("utf-8")
        	remarks = request.args.get('remarks').encode("utf-8")
                owner = request.args.get('owner').encode("utf-8")
                runstatus = request.args.get('runstatus').encode("utf-8")
        	sql = 'insert into vms (devicetype, vmhostip, serstyle, busstyle, cpunum, memsize, disk, disksize, diskgt, insidecard, insideip, codeenv, owner, runstatus, remarks) values ("%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s")' % (devicetype.strip(), vmhostip.strip(), serstyle.strip(), busstyle.strip(), cpunum.strip(), memsize.strip(), disk.strip(), disksize.strip(), diskgt, insidecard.strip(), insideip.strip(), codeenv, owner.strip(), runstatus.strip(), remarks.strip())
        	sqlinit(sql)
        	o['info'] = '<p><span style="color:blue;font-weight:bold"> 虚拟机添加成功，IP地址：%s</span></p>' % insideip
        	return json.dumps(o)
        elif cmdbtype == 'netdevice':
        	o = {}
        	o['status'] = 1
        	ndname = request.args.get('ndname').encode("utf-8")
        	ndstyle = request.args.get('ndstyle').encode("utf-8")
        	ndassetlabel = request.args.get('ndassetlabel').encode("utf-8")
        	ndrack = request.args.get('ndrack').encode("utf-8")
        	ndaddr = request.args.get('ndaddr').encode("utf-8")
        	ndnote = request.args.get('ndnote').encode("utf-8")
		owner = request.args.get('owner').encode("utf-8")
		runstatus = request.args.get('runstatus').encode("utf-8")
        	sql = 'insert into netdevices (ndrack, ndaddr, ndname, ndstyle, ndassetlabel, ndnote, devicetype, owner, runstatus) values ("%s","%s","%s","%s","%s","%s","%s","%s","%s")' % (ndrack.strip(), ndaddr.strip(), ndname.strip(), ndstyle.strip(), ndassetlabel.strip(), ndnote.strip(), '网络设备', owner.strip(), runstatus.strip())
        	try:
                	sqlinit(sql)
                	o['status'] = 0
        		o['info'] = '<p><span style="color:blue;font-weight:bold"> %s 添加成功！</span></p>' % ndassetlabel
        	except:
                	pass
        	return json.dumps(o)
        elif cmdbtype == 'ndport':
                ndname = request.args.get('ndname').encode("utf-8")
                ndport = request.args.get('ndport').encode("utf-8")
                ndvlan = request.args.get('ndvlan').encode("utf-8")
                ndipaddr = request.args.get('ndipaddr').encode("utf-8")
                linkndname = request.args.get('linkndname').encode("utf-8")
                linkndport = request.args.get('linkndport').encode("utf-8")
                linkndaddr = request.args.get('linkndaddr').encode("utf-8")
                sql1 = 'insert into ndports (ndname, ndport, ndvlan, ndipaddr, ndlinknd, linkndport, linkndipaddr) values ("%s","%s","%s","%s","%s","%s","%s")' % (ndname.strip(), ndport.strip(), ndvlan.strip(), ndipaddr.strip(), linkndname.strip(), linkndport.strip(), linkndaddr.strip())
                sqlinit(sql1)
                sql2 = 'insert into ndports (ndname, ndport, ndvlan, ndipaddr, ndlinknd, linkndport, linkndipaddr) values ("%s","%s","%s","%s","%s","%s","%s")' % (linkndname.strip(), linkndport.strip(), ndvlan.strip(), linkndaddr.strip(), ndname.strip(), ndport.strip(), ndipaddr.strip())
                sqlinit(sql2)
                return json.dumps('ok')

@cmdbpg.route('/cmdb/query')
def cmdbquery():
	cmdbtype = request.args.get('cmdbtype')
	if cmdbtype == 'idc':
		o = {
        	'status':1,
        	'table_str':'',
        	'total_page':'',
        	'pagation_str':''
        	}
		init_str = ''
        	sqlidcname = 'select idcname from idcs'
        	sqlrz = sqlinit(sqlidcname)
        	for idcs in sqlrz:
        		sqlracknum = 'select rackname from racks where idcname = \"%s\" ' % (idcs[0])
        		rz = sqlinit(sqlracknum)
        		racksnum = len(rz)
        		# 修改机房的机柜数
        		udracksum = 'update idcs set racksnum = \"%s\" where idcname = \"%s\" ' % (racksnum,idcs[0])
        		sqlinit(udracksum)
        		hostsnum, sevnum, ndnum = 0, 0, 0
        		
        		for rack in rz:		
        			sqlsevnum = 'select count(*) from hosts where hrack = \"%s\" ' % (rack[0])
        			sqlndnum = 'select count(*) from netdevices where ndrack = \"%s\" ' % (rack[0])
        			snum = sqlinit(sqlsevnum)[0]
        			nnum = sqlinit(sqlndnum)[0]
        			# 修改机柜的主机数
        			udrackhostnum = 'update racks set hostsnum = \"%s\" where rackname = \"%s\" ' % (snum[0] + nnum[0], rack[0])
        			sqlinit(udrackhostnum)
        			# 服务器数/网络设备数自增
        			sevnum = sevnum + snum[0]
        			ndnum = ndnum + nnum[0]
        		# 修改机房的主机数
        		udidchostnum = 'update idcs set hostsnum = \"%s\" where idcname = \"%s\" ' % (sevnum + ndnum, idcs[0])
        		sqlinit(udidchostnum)
        		
        	sql = 'select * from idcs order by id '
        	sqlrz = sqlinit(sql)
        	for c in sqlrz:
                	init_str = init_str + '''<tr><td><a style="font-size:15px;font-weight:bold" href="/cmdb/idcracks/%s">%s</a></td><td><font size="3" face="arial" color="black">%s</font></td><td><font size="3" face="arial" color="black">%s</font></td><td>%s</td><td>%s</td><td>%s / %s</td><td>%s</td>
        				<td>
                                        <button data-id="%s" class="btn btn-warning dlt">删除</button>&nbsp
                                        <button data-id="%s" class="btn btn-info update">修改</button>
                                        </td></tr>''' % (c[1],c[1],c[2],c[3],c[4],c[5],c[6],c[7],c[8],c[0],c[0])
        	o['table_str'] = init_str
        
        	return json.dumps(o)
        if cmdbtype == 'rack':
                if idc_queue.empty():
                        return "you need to access '/cmdb/idcracks/<idname>' first"
                else:
                        idcname = idc_queue.get()
        
        	page = int(request.args.get('page',1))
        	count = request.args.get('count',10)
        
        	o = {
                'status':1,
                'table_str':'',
                'total_page':'',
                'pagation_str':''
        	}   
        
        	init_str = ''
        	count_sql = 'select count(*) from racks where idcname = \"%s\" ' % idcname
        	total = sqlinit(count_sql)[0][0]
        	o['total_page'] = total/count+1
        	if page == -1:	#如果ajax传过来的"-1",就给它返回最后一页
        		page = o['total_page']
        	#sql = 'select * from racks where idcname = \"%s\" order by id limit %s,%s' % (idcname,(page-1)*count,count)
        	sql = 'select id, rackname, hostsnum, rackaddr, racksize, racknote from racks where idcname = \"%s\" order by id ' % (idcname)
        	for c in sqlinit(sql):
                	init_str = init_str + '''<tr><td><a style="font-size:15px;font-weight:bold" href="/cmdb/rackhosts/%s">%s</a></td><td><font size="3" face="arial" color="black">%s</font></td><td>%s</td><td>%s</td><td>%s</td>
        				<td>
                                        <button data-id="%s" class="btn btn-warning dlt">删除</button>&nbsp
                                        <button data-id="%s" class="btn btn-info update">修改</button>
                                        </td></tr>''' % (c[1],c[1],c[2],c[3],c[4],c[5],c[0],c[0])
        	o['table_str'] = init_str
        
        	page_str = ''
        	if page > 1:
                	page_str = page_str + '''
                                        <li data-page="%s" class="page-reboot">
                                            <a href="#">上一页</a></li> 
                                '''%(page-1)
        	for i in range(1,o['total_page']+1):
                	if i==page:     
                		page_str = page_str+'''
                                        <li class="active page-reboot" data-page="%s">
                                            <a href="#">%s</a></li> 
                                '''%(i,i)
                	else:
                		page_str = page_str+'''
                                        <li data-page="%s" class="page-reboot">
                                            <a href="#">%s</a></li> 
                                '''%(i,i)
        	if page < o['total_page']:
        		page_str = page_str + '''
                                        <li data-page="%s" class="page-reboot">
                                            <a href="#">下一页</a></li> 
                                '''%(page+1)
        
        	o['pagation_str'] = page_str
        	return json.dumps(o)
	elif cmdbtype == 'host':
        	if rack_queue.empty():
            		return "you need to access '/cmdb/rackhosts/<idname>' first"
        	else:
                	rackname = rack_queue.get()
        
        	o = {
                'status':1,
                'table_str':'',
                'total_page':'',
                'pagation_str':''
        	}   
        
        	init_str = ''
        	sql0 = 'select id, ndrack, ndaddr, ndstyle, ndassetlabel, owner, runstatus, ndname from netdevices where ndrack = \"%s\" order by ndaddr desc' % (rackname)
        	ndinfo = sqlinit(sql0)
        	for n in ndinfo:
			if n[6] == "离线":
				status = " <button class='btn btn-warning'> 离线 </button> "
			elif n[6] == "在线":
				status = " <button class='btn btn-success'> 在线 </button> "
        		init_str = init_str + racknetdevicesqueryformat % (n[2], n[3], '网络设备', '', '', '', '', '', '', '', '', '', n[4], n[5], status, n[7], n[0], n[1], 'netdevice', n[0], n[1], 'netdevice')
        
        	sql = 'select * from hosts where hrack = \"%s\" order by sitecode desc' % (rackname)
        	sqlrz = sqlinit(sql)
        	for c in sqlrz:
			if c[33] == "离线":
				status = " <button class='btn btn-warning'> 离线 </button> "
			elif c[33] == "在线":
				status = " <button class='btn btn-success'> 在线 </button> "
        		init_str = init_str + rackhostsqueryformat % (c[2],c[3],c[28],c[5],c[6],c[7],c[8],c[9],c[10],c[11],c[12],c[13],c[14],c[14],c[15],c[16], c[17],c[18],c[19],c[19],c[20],c[21],c[22],c[23],c[24],c[24],c[25],c[26],c[28],c[29],c[30],c[31],c[32],status,c[34],c[0],c[1],'phy',c[0],c[1],'phy')
        
        	o['table_str'] = init_str
        	return json.dumps(o)
        elif cmdbtype == 'netdevice':
       		# 2种方式：请求接口传参数ndname，不传参数而通过队列获取ndname
        	ndname = request.args.get('ndname')
        	if ndname == None:
        		if nd_queue.empty():
        			return "you need to access '/cmdb/rackhosts/<idname>' first"
        		else:
        			ndname = nd_queue.get()
        	o = {
                'status':1,
        	'ndname':'',
                'table_str1':'',
                'table_str2':'',
                'total_page':'',
                'pagation_str':''
        	} 
        	o['ndname'] = ndname
          
        	init_str1 = ''
        	sql1 = 'select ndrack, ndaddr, ndname, ndstyle, ndassetlabel, owner, runstatus, ndnote from netdevices where ndname = \"%s\" ' % (ndname)
        	sqlrz1 = sqlinit(sql1)
        	for c in sqlrz1:
        		init_str1 = init_str1 + '''<tr><td><a style="font-size:15px;font-weight:bold" href="/cmdb/rackhosts/%s">%s</a> / %s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>''' % (c[0],c[0],c[1],c[2],c[3],c[4],c[5],c[6],c[7])
        	o['table_str1'] = init_str1
        
        	init_str2 = ''
        	sql2 = 'select id, ndport, ndvlan, ndipaddr, ndlinknd, linkndport, linkndipaddr from ndports where ndname = \"%s\" ' % (ndname)
        	sqlrz2 = sqlinit(sql2)
        	for c in sqlrz2:
        		init_str2 = init_str2 + ''' <tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td>
        				<td>
                                        <button data-id="%s" class="btn btn-warning dlt">删除</button>&nbsp
                                        </td></tr>''' % (c[1],c[2],c[3],c[4],c[5],c[6],c[0])
        	o['table_str2'] = init_str2
        	return json.dumps(o)
        elif cmdbtype == 'vmhost':
        	o = {
        'status':1,
        'table_str':'',
        'total_page':'',
        'pagation_str':'',
	'hostsnum':'',
        }

        	init_str = ''
                sql = 'select * from hosts where devicetype = "虚拟化/宿主机" '
                sqlrz = sqlinit(sql)
                for c in sqlrz:
			if c[33] == "离线":
				status = " <button class='btn btn-warning'> 离线 </button> "
			elif c[33] == "在线":
				status = " <button class='btn btn-success'> 在线 </button> "
                        sql = 'select count(*) from vms where vmhostip = "%s" and codeenv = "%s" ' % (c[14], c[31])
                        vmsnum = sqlinit(sql)[0][0]
                        init_str = init_str + ''' 
<tr>
<td><a style="font-size:15px;font-weight:bold" href="/cmdb/rackhosts/%s">%s</a> / %s</td>
<td>%s</td>
<td><a style="font-size:15px;font-weight:bold" href="/cmdb/vms/%s_%s"> %s </a></td>
<td><font size="3" face="arial" color="black">%s</font></td>
<td>%s</td>
<td>%s*%sGB</td>
<td>%s*%s%s / %s</td>
<td>%s / %s /<a style="font-size:15px;font-weight:bold" href="/cmdb/netdevice/%s"> %s </a>/ %s / %s </td>
<td>%s / %s /<a style="font-size:15px;font-weight:bold" href="/cmdb/netdevice/%s"> %s </a>/ %s / %s </td>
<td>%s / %s /<a style="font-size:15px;font-weight:bold" href="/cmdb/netdevice/%s"> %s </a>/ %s / %s </td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td>
<button data-id="%s" rack-name="%s" objecttype="%s" class="btn btn-warning dlt">删除</button>&nbsp
<button data-id="%s" rack-name="%s" objecttype="%s" class="btn btn-info update">修改</button>
</td>
</tr>

''' % (c[1],c[1],c[2],c[3],c[13],c[30],c[27],vmsnum,c[5],c[6],c[7],c[8],c[9],c[10],c[11],c[12],c[13],c[14],c[14],c[15],c[16], c[17],c[18],c[19],c[19],c[20],c[21],c[22],c[23],c[24],c[24],c[25],c[26],c[28],c[29],c[30],c[31],c[32],status,c[34],c[0],c[1],'vmhost',c[0],c[1],'vmhost')

                o['table_str'] = init_str
                o['hostsnum'] =  '''<p style="font-size:20px;font-weight:bold"> 宿主机个数：<font size="5" face="arial" color="blue">%s</font></p>''' % (len(sqlrz))
                return json.dumps(o)
        elif cmdbtype == 'netdevicesall':
	        o = {
        'status':1,
        'table_str':'',
        'total_page':'',
        'pagation_str':'',
	'hostsnum':'',
        }
        	init_str = ''
                sql = 'select id, ndrack, ndaddr, ndname, ndstyle, ndassetlabel, devicetype, owner, runstatus, ndnote from netdevices'
                sqlrz = sqlinit(sql)
                for c in sqlrz:
			if c[8] == "离线":
				status = " <button class='btn btn-warning'> 离线 </button> "
			if c[8] == "在线":
				status = " <button class='btn btn-success'> 在线 </button> "
                        init_str = init_str + '''<tr><td><a style="font-size:15px;font-weight:bold" href="/cmdb/rackhosts/%s">%s</a> / %s</td><td><a style="font-size:15px;font-weight:bold" href="/cmdb/netdevice/%s"> %s </a></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>
<button data-id="%s" rack-name="%s" objecttype="%s" class="btn btn-warning nddlt">删除</button>&nbsp
<button data-id="%s" rack-name="%s" objecttype="%s" class="btn btn-info ndupdate">修改</button>
</td></tr> ''' % (c[1],c[1],c[2],c[3],c[3],c[4],c[5],c[7],status,c[9],c[0],c[1],c[6],c[0],c[1],c[6])
                o['table_str'] = init_str
                return json.dumps(o)
        elif cmdbtype == 'phymachine':
		page = int(request.args.get('page',1))
        	count = request.args.get('count',10)

        	o = {
        'status':1,
        'table_str':'',
        'total_page':'',
        'pagation_str':'',
	'hostsnum':'',
        }

        	count_sql = 'select count(*) from hosts where devicetype = "物理机" '
        	total = sqlinit(count_sql)[0][0]
        	o['total_page'] = total/count+1
        	if page == -1:  #如果ajax传过来的"-1",就给它返回最后一页
                	page = o['total_page']
        	init_str = ''
                sql = 'select * from hosts where devicetype = "物理机" order by id limit %s,%s ' % ((page-1)*count,count)
                sqlrz = sqlinit(sql)
                for c in sqlrz:
			if c[33] == "离线":
				status = " <button class='btn btn-warning'> 离线 </button> "
			elif c[33] == "在线":
				status = " <button class='btn btn-success'> 在线 </button> "
                        init_str = init_str + hostsqueryformat % (c[1],c[1],c[2],c[3],c[27],c[5],c[6],c[7],c[8],c[9],c[10],c[11],c[12],c[13],c[14],c[14],c[15],c[16], c[17],c[18],c[19],c[19],c[20],c[21],c[22],c[23],c[24],c[24],c[25],c[26],c[28],c[29],c[30],c[31],c[32],status,c[34],c[0],c[1],'physicalmachine',c[0],c[1],'physicalmachine')
                o['table_str'] = init_str
                o['hostsnum'] =  '''<p style="font-size:20px;font-weight:bold"> 物理机个数：<font size="5" face="arial" color="blue">%s</font></p>''' % (total)

		page_str = ''
        	if page > 1:
                	page_str = page_str + '''
                                <li data-page="%s" class="page-reboot">
                                    <a href="#">上一页</a></li> 
                        '''%(page-1)
        	for i in range(1,o['total_page']+1):
                	if i==page:
                        	page_str = page_str+'''
                                <li class="active page-reboot" data-page="%s">
                                    <a href="#">%s</a></li> 
                        '''%(i,i)
                	else:
                        	page_str = page_str+'''
                                <li data-page="%s" class="page-reboot">
                                    <a href="#">%s</a></li> 
                        '''%(i,i)
        	if page < o['total_page']:
                	page_str = page_str + '''
                                <li data-page="%s" class="page-reboot">
                                    <a href="#">下一页</a></li> 
                        '''%(page+1)
        	o['pagation_str'] = page_str
                return json.dumps(o)

        elif cmdbtype == 'vms':
                o = {
                'status':1,
                'table_str':'',
                'total_page':'',
                'pagation_str':'',
                }
                if vm_queue.empty():
                        return "you need to access '/cmdb/vms/<ip_env>' first"
                else:
                        ip_env = vm_queue.get()
                vmhostip, env = ip_env.split('_')[0], ip_env.split('_')[1]
                sql = 'select id, devicetype, cpunum, memsize, disk, disksize, diskgt, insidecard, insideip, serstyle, busstyle, codeenv, vmhostip, remarks, owner, runstatus from vms where vmhostip = "%s" and codeenv = "%s" ' % (vmhostip, env)
                sqlrz = sqlinit(sql)
                init_str = ''
                for c in sqlrz:
			if c[15] == "离线":
                                status = " <button class='btn btn-warning'> 离线 </button> "
                        elif c[15] == "在线":
                                status = " <button class='btn btn-success'> 在线 </button> "
                        init_str = init_str + ''' 
        <tr>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s * %s%s</td>
        <td>%s / %s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>
        <button data-id="%s" objecttype="%s" vmhostinfo="%s_%s" class="btn btn-warning vmsdlt">删除</button>&nbsp
        <button data-id="%s" objecttype="%s" vmhostinfo="%s_%s" class="btn btn-info vmsupdate">修改</button>
        </td>
        </tr> 
        ''' % (c[1],c[2],c[3],c[4],c[5],c[6],c[7],c[8],c[9],c[10],c[11],c[12],c[14],status,c[13],c[0],c[1],c[12],c[11],c[0],c[1],c[12],c[11])
                o['table_str'] = init_str
                return json.dumps(o)


############################### inputautoapi ##########################

@cmdbpg.route('/cmdb/inputautoapi')
def cmdbinputautoapi():
	cmdbipt = request.args.get('cmdbipt')
	if cmdbipt == 'devicetype':
		data = 'Dell R710','Dell R720','Dell R910'
	elif cmdbipt == 'linkswt':
		data = 'DC1-N2K-1','DC1-N2K-2','DC1-N3K-1','DC1-N3K-2','DC1-N5K-1','DC1-N5K-2','DC1-N7K-1','DC1-N7K-1'
	elif cmdbipt == 'nd':
		data = 'Cisco N2K-C2348UPQF','Cisco N2K-C2348UPQ4F','Cisco N5K-C5696Q','Cisco N7K-M148GS-11','Cisco N7K-M148GT-11'
	else:
		pass
	return json.dumps(data)

############################### Excel download ##########################

@cmdbpg.route('/cmdb/download/<filename>')
def cmdbdownload(filename):
	if filename == "sou.xls":
		return send_from_directory(UPLOAD_FOLDER, filename)
	elif filename == "idc.xls":
		row1 = (u'所在机柜', u'在机柜的位置', u'设备型号', u'机型', u'CPU核数', u'内存个数', u'单内存大小（G）', u'磁盘个数', u'磁盘大小', u'磁盘容量单位', u'raid级别', u'网卡1', u'ip', u'交换机', u'交换机端口', u'vlan', u'网卡2', u'ip', u'交换机', u'交换机端口', u'vlan', u'管理网卡', u'管理ip', u'管理交换机', u'管理端口', u'vlan', u'主机类型',u'poll类型', u'业务类型', u'代码环境', u'SN号', u'责任人', u'运行状态', u'备注')
                book_write = xlwt.Workbook()    #创建excel对象
                book_write.add_sheet(u'物理机')    #创建sheet名为 物理机
                book_write.add_sheet(u'宿主机')    #创建sheet名为 宿主机
                book_write.add_sheet(u'网络设备')    #创建sheet名为 网络设备
                sheet1 = book_write.get_sheet(0)        #获取sheet1
		sheet2 = book_write.get_sheet(1)
		sheet3 = book_write.get_sheet(2)

		# sheet1
                for r in range(len(row1)):
                        sheet1.write(0,r,row1[r])

                sql = "select hrack, hsite, devstyle, usize, cpunum, memnum, memsize, disk, disksize, diskgt, raid, insidecard, insideip, insidesw, iport, ivlan, outsidecard, outsideip, outsidesw, oport, ovlan, mngcard, mngip, mngsw, mngport, mngvlan, devicetype, osversion, busstyle, codeenv, assetnumber, owner, runstatus, remarks from hosts where devicetype = '%s' order by hsite desc " % ('物理机')
                rz = sqlinit(sql)
                for i in range(1, len(rz) + 1):
                        row_data = rz[i-1]     #第i行的值
                        for j in range(len(row_data)):
                                sheet1.write(i,j,row_data[j])     #第i+n行第j+1个的值为：row_data[j]

		# sheet2
                for r in range(len(row1)):
                        sheet2.write(0,r,row1[r])

                sql = "select hrack, hsite, devstyle, usize, cpunum, memnum, memsize, disk, disksize, diskgt, raid, insidecard, insideip, insidesw, iport, ivlan, outsidecard, outsideip, outsidesw, oport, ovlan, mngcard, mngip, mngsw, mngport, mngvlan, devicetype, osversion, busstyle, codeenv, assetnumber, owner, runstatus, remarks from hosts where devicetype = '%s' order by hsite desc " % ('虚拟化/宿主机')
                rz = sqlinit(sql)
                for i in range(1, len(rz) + 1):
                        row_data = rz[i-1]     #第i行的值
                        for j in range(len(row_data)):
                                sheet2.write(i,j,row_data[j])     #第i+n行第j+1个的值为：row_data[j]

		# sheet3
		row1 = (u'所在机柜', u'在机柜的位置', u'设备名', u'设备型号', u'SN号', u'设备类型', u'责任人', u'运行状态', u'备注')

                for r in range(len(row1)):
                        sheet3.write(0,r,row1[r])

                sql = 'select ndrack, ndaddr, ndname, ndstyle, ndassetlabel, devicetype, owner, runstatus, ndnote from netdevices'
                rz = sqlinit(sql)
                for i in range(1, len(rz) + 1):
                        row_data = rz[i-1]     #第i行的值
                        for j in range(len(row_data)):
                                sheet3.write(i,j,row_data[j])     #第i+n行第j+1个的值为：row_data[j]
                book_write.save(UPLOAD_FOLDER + filename)     #把该excel保存为filename
                return send_from_directory(UPLOAD_FOLDER, filename)

	elif re.findall('^idc_', filename):
		idcname = re.split(u'_|\.',filename)[1]
		row1 = (u'机柜', u'主机数', u'地理位置', u'机柜大小', u'备注')
		book_write = xlwt.Workbook()    #创建excel对象
		book_write.add_sheet(filename)    #创建sheet(名为filename
		sheet1 = book_write.get_sheet(0)        #获取sheet1)

		for r in range(len(row1)):
			sheet1.write(0,r,row1[r])

		sql = "select rackname, hostsnum, rackaddr, racksize, racknote from racks where idcname = '%s' ORDER BY id;" % idcname
		rz = sqlinit(sql)
		
                for i in range(1, len(rz) + 1):
                        row_data = rz[i-1]     #第i行的值
                        for j in range(len(row_data)):
                                sheet1.write(i,j,row_data[j])     #第i行第j+1个的值为：row_data[j]
                book_write.save(UPLOAD_FOLDER + filename)     #把该excel保存为filename
                return send_from_directory(UPLOAD_FOLDER, filename)
	elif re.findall('_rack', filename):
		rackname = re.split(u'\.',filename)[0]
		row1 = (u'所在机柜', u'在机柜的位置', u'设备型号', u'机型', u'CPU核数', u'内存个数', u'单内存大小（G）', u'磁盘个数', u'磁盘大小', u'磁盘容量单位', u'raid级别', u'网卡1', u'ip', u'交换机', u'交换机端口', u'vlan', u'网卡2', u'ip', u'交换机', u'交换机端口', u'vlan', u'管理网卡', u'管理ip', u'管理交换机', u'管理端口', u'vlan', u'主机类型', u'poll类型', u'业务类型', u'代码环境', u'SN号', u'责任人', u'运行状态', u'备注')
		book_write = xlwt.Workbook()    #创建excel对象
                book_write.add_sheet(filename)    #创建sheet(名为filename
                sheet1 = book_write.get_sheet(0)        #获取sheet1)

                for r in range(len(row1)):
                        sheet1.write(0,r,row1[r])
		
		sqlnd = "select ndrack, ndaddr, ndstyle, devicetype, owner, runstatus, ndnote from netdevices order by ndaddr desc "
		rz = sqlinit(sqlnd)
                for n in range(1, len(rz) + 1):
                        row_data = rz[n-1]     #第i行的值
                        sheet1.write(n,0,row_data[0])     #第i行第j+1个的值为：row_data[j]
			sheet1.write(n,1,row_data[1])
			sheet1.write(n,2,row_data[2])
			sheet1.write(n,31,row_data[3])
			sheet1.write(n,32,row_data[4])
			sheet1.write(n,33,row_data[5])
			sheet1.write(n,34,row_data[6])

		sqlser = "select hrack, hsite, devstyle, usize, cpunum, memnum, memsize, disk, disksize, diskgt, raid, insidecard, insideip, insidesw, iport, ivlan, outsidecard, outsideip, outsidesw, oport, ovlan, mngcard, mngip, mngsw, mngport, mngvlan, devicetype, osversion, busstyle, codeenv, assetnumber, owner, runstatus, remarks from hosts where hrack = '%s' order by hsite desc " % rackname
		rz = sqlinit(sqlser)
                for i in range(1, len(rz) + 1):
                        row_data = rz[i-1]     #第i行的值
                        for j in range(len(row_data)):
                                sheet1.write(i+n,j,row_data[j])     #第i+n行第j+1个的值为：row_data[j]
                book_write.save(UPLOAD_FOLDER + filename)     #把该excel保存为filename
                return send_from_directory(UPLOAD_FOLDER, filename)
	elif filename == '物理机.xls':
		row1 = (u'所在机柜', u'在机柜的位置', u'设备型号', u'机型', u'CPU核数', u'内存个数', u'单内存大小（G）', u'磁盘个数', u'磁盘大小', u'磁盘容量单位', u'raid级别', u'网卡1', u'ip', u'交换机', u'交换机端口', u'vlan', u'网卡2', u'ip', u'交换机', u'交换机端口', u'vlan', u'管理网卡', u'管理ip', u'管理交换机', u'管理端口', u'vlan', u'主机类型', u'poll类型', u'业务类型', u'代码环境', u'SN号', u'责任人', u'运行状态', u'备注')
                book_write = xlwt.Workbook()    #创建excel对象
                book_write.add_sheet(filename)    #创建sheet(名为filename
                sheet1 = book_write.get_sheet(0)        #获取sheet1)

                for r in range(len(row1)):
                        sheet1.write(0,r,row1[r])

		sql = "select hrack, hsite, devstyle, usize, cpunum, memnum, memsize, disk, disksize, diskgt, raid, insidecard, insideip, insidesw, iport, ivlan, outsidecard, outsideip, outsidesw, oport, ovlan, mngcard, mngip, mngsw, mngport, mngvlan, devicetype, osversion, busstyle, codeenv, assetnumber, owner, runstatus, remarks from hosts where devicetype = '%s' order by hsite desc " % ('物理机')
		rz = sqlinit(sql)
                for i in range(1, len(rz) + 1):
                        row_data = rz[i-1]     #第i行的值
                        for j in range(len(row_data)):
                                sheet1.write(i,j,row_data[j])     #第i+n行第j+1个的值为：row_data[j]
                book_write.save(UPLOAD_FOLDER + filename)     #把该excel保存为filename
                return send_from_directory(UPLOAD_FOLDER, filename)
        elif filename == '宿主机.xls':
		row1 = (u'所在机柜', u'在机柜的位置', u'设备型号', u'机型', u'CPU核数', u'内存个数', u'单内存大小（G）', u'磁盘个数', u'磁盘大小', u'磁盘容量单位', u'raid级别', u'网卡1', u'ip', u'交换机', u'交换机端口', u'vlan', u'网卡2', u'ip', u'交换机', u'交换机端口', u'vlan', u'管理网卡', u'管理ip', u'管理交换机', u'管理端口', u'vlan', u'主机类型', u'poll类型', u'业务类型', u'代码环境', u'SN号', u'责任人', u'运行状态', u'备注')
                book_write = xlwt.Workbook()    #创建excel对象
                book_write.add_sheet(filename)    #创建sheet(名为filename
                sheet1 = book_write.get_sheet(0)        #获取sheet1)

                for r in range(len(row1)):
                        sheet1.write(0,r,row1[r])

		sql = "select hrack, hsite, devstyle, usize, cpunum, memnum, memsize, disk, disksize, diskgt, raid, insidecard, insideip, insidesw, iport, ivlan, outsidecard, outsideip, outsidesw, oport, ovlan, mngcard, mngip, mngsw, mngport, mngvlan, devicetype, osversion, busstyle, codeenv, assetnumber, owner, runstatus, remarks from hosts where devicetype = '%s' order by hsite desc " % ('虚拟化/宿主机')
                rz = sqlinit(sql)
                for i in range(1, len(rz) + 1):
                        row_data = rz[i-1]     #第i行的值
                        for j in range(len(row_data)):
                                sheet1.write(i,j,row_data[j])     #第i+n行第j+1个的值为：row_data[j]
                book_write.save(UPLOAD_FOLDER + filename)     #把该excel保存为filename
                return send_from_directory(UPLOAD_FOLDER, filename)
	elif filename == '网络设备.xls':
		row1 = (u'所在机柜', u'在机柜的位置', u'设备名', u'设备型号', u'SN号', u'设备类型', u'责任人', u'运行状态', u'备注')
                book_write = xlwt.Workbook()    #创建excel对象
                book_write.add_sheet(filename)    #创建sheet(名为filename
                sheet1 = book_write.get_sheet(0)        #获取sheet1)

                for r in range(len(row1)):
                        sheet1.write(0,r,row1[r])
		
		sql = 'select ndrack, ndaddr, ndname, ndstyle, ndassetlabel, devicetype, owner, runstatus, ndnote from netdevices'
		rz = sqlinit(sql)
                for i in range(1, len(rz) + 1):
                        row_data = rz[i-1]     #第i行的值
                        for j in range(len(row_data)):
                                sheet1.write(i,j,row_data[j])     #第i+n行第j+1个的值为：row_data[j]
                book_write.save(UPLOAD_FOLDER + filename)     #把该excel保存为filename
                return send_from_directory(UPLOAD_FOLDER, filename)

@cmdbpg.route('/cmdb/sou')
def cmdbsou():
	sdata = request.args.get('searchstr').strip()
	sdata = sdata.encode("utf-8") 
	sou_queue.put(sdata)
	return 'ok'

@cmdbpg.route('/cmdb/souweb')
def cmdbsouweb():
        label = request.args.get('checklabel')
	if label == 'web':
		return render_template('cmdbpg/search.html')
        elif label == 'xinops':
                sdata = sou_queue.get()
        	o = {
	        'status':1,
        	'table_str':'',
	        'total_page':'',
        	'pagation_str':'',
		'souword':'',
		'sounum':'',
        	}
		if sdata == '' or sdata.isspace():
			o['souword'] = '''<p style="font-size:20px;font-weight:bold"> 搜索的字段：<font size="5" face="arial" color="blue">%s</font> </p>''' % sdata
			o['sounum'] = '''<p style="font-size:20px;font-weight:bold"> 搜到的记录数：<font size="5" face="arial" color="blue">%d</font> </p>''' % 0
			return json.dumps(o)
		init_str = ''
		sounet = []
		souser = []
		ndsql = 'select id, ndrack, ndaddr, ndname, ndstyle, ndassetlabel, devicetype, owner, runstatus, ndnote from netdevices'
		rz = sqlinit(ndsql)
                for i in rz:
                        nddata = [j.encode("utf-8") for j in i[1:]]
                        if re.findall(sdata,''.join(nddata)):
                        	if i[8] == "离线":
					status = " <button class='btn btn-warning'> 离线 </button> "
				elif i[8] == "在线":
					status = " <button class='btn btn-success'> 在线 </button> "
				ndsite = '<a style="font-size:15px;font-weight:bold" href="/cmdb/rackhosts/%s">%s</a> / %s' % (i[1], i[1], i[2])
				init_str = init_str + racknetdevicesqueryformat % (ndsite, i[4], '网络设备', '', '', '', '', '', '', '', '', '', i[5], i[7], status, i[3], i[0], i[1], 'netdevice', i[0], i[1], 'netdevice')
				i = list(i)
				del i[0]
				del i[3]
				sounet.append(i)
		sersql = 'select * from hosts'
		rz = sqlinit(sersql)
		for i in rz:
			serdata = [j.encode("utf-8") for j in i[1:]]
			if re.findall(sdata,''.join(serdata)):
				#souser.append(i)
				if i[33] == "离线":
					status = " <button class='btn btn-warning'> 离线 </button> "
				elif i[33] == "在线":
					status = " <button class='btn btn-success'> 在线 </button> "
        			init_str = init_str + hostsqueryformat % (i[1], i[1], i[2], i[3], i[27], i[5], i[6], i[7], i[8], i[9], i[10], i[11], i[12], i[13], i[14], i[14], i[15], i[16], i[17], i[18], i[19], i[19], i[20], i[21], i[22], i[23], i[24], i[24], i[25], i[26], i[28], i[29], i[30], i[31], i[32], status, i[34], i[0], i[1], 'phy', i[0], i[1], 'phy')
				i = list(i)
				del i[0]
				del i[-1]
				souser.append(i)
		o['table_str'] = init_str
		o['souword'] = '''<p style="font-size:20px;font-weight:bold"> 搜索的字段：<font size="5" face="arial" color="blue">%s</font> </p>''' % sdata
		o['sounum'] = '''<p style="font-size:20px;font-weight:bold"> 搜到的记录数：<font size="5" face="arial" color="blue">%d</font> </p>''' % (len(sounet) + len(souser))
                # create xls file 
		row1 = (u'所在机柜', u'在机柜的位置', u'设备型号', u'机型', u'CPU核数', u'内存个数', u'单内存大小（G）', u'磁盘个数', u'磁盘大小', u'磁盘容量单位', u'raid级别', u'网卡1', u'ip', u'交换机', u'交换机端口', u'vlan', u'网卡2', u'ip', u'交换机', u'交换机端口', u'vlan', u'管理网卡', u'管理ip', u'管理交换机', u'管理端口', u'vlan', u'主机类型',u'poll类型', u'业务类型', u'代码环境', u'SN号', u'责任人', u'运行状态', u'备注')
		book_write = xlwt.Workbook() 
		book_write.add_sheet(u'search') 
		sheet1 = book_write.get_sheet(0)
		for r in range(len(row1)):
			sheet1.write(0,r,row1[r])

		for i in range(1, len(sounet) + 1):
			row_data = sounet[i-1]     #第i行的值
			sheet1.write(i,0,row_data[0])
			sheet1.write(i,1,row_data[1])
			sheet1.write(i,2,row_data[2])
			sheet1.write(i,31,row_data[3])
			sheet1.write(i,27,row_data[4])
			sheet1.write(i,32,row_data[5])
			sheet1.write(i,33,row_data[6])
			sheet1.write(i,34,row_data[7])
		#	sheet1.write(i,34,row_data[7])

                for i in range(1, len(souser) + 1):
                        row_data = souser[i-1]     #第i行的值
                        for j in range(len(row_data)):
                                sheet1.write(i + len(sounet),j,row_data[j]) 

		book_write.save(UPLOAD_FOLDER + 'sou.xls') 		
		return json.dumps(o)
        else:
                return 'error...'

