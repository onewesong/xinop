#!/usr/bin/env python
#coding=utf-8


import sys
reload(sys)
sys.setdefaultencoding('utf8')
sys.path.append("..")

import re, os, json, time, datetime, MySQLdb
from flask import Flask,request,render_template,Blueprint
from config.sql import sqlinit
zbxpg = Blueprint('zbxpg',__name__,template_folder='templates',static_folder='static')

def pagehtml(page_html, page, page1, page2):
        for i in range(page1, page2):
                if i == page:
                        page_html = page_html + ''' <li class="active page-reboot" data-page="%s"><a href="#">%s</a></li> ''' % (i, i)
                else:
                        page_html = page_html + ''' <li data-page="%s" class="page-reboot"><a href="#">%s</a></li> ''' % (i, i)
        return page_html

@zbxpg.route('/zbxquery/zbxindex')
def zbxqueryzbxindex():
	return render_template('zbxpages/zbxindex.html')

@zbxpg.route('/zbxquery/monquery')
def zbxquerymonquery():
        # 接收前端的输入
        page = int(request.args.get('page',1))
        count = request.args.get('count').encode("utf-8")
        if count == '每页10条':
                count = 10
        elif count == '每页50条':
                count = 50
        elif count == '每页100条':
                count = 100
        test1 = request.args.get('test1')
        showinfo = request.args.get('showinfo')
        if showinfo == 'showinfo':
                return '1...'
        modname = request.args.get('modname').encode("utf-8").strip()
        dateinfo = request.args.get('dateinfo').encode("utf-8")
        timedate = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())).split()[1]
        if dateinfo == '1天' :
                timed = 1
        elif dateinfo == '3天' :
                timed = 3
        elif dateinfo == '7天' :
                timed = 7
        # 第一次过滤（按日期）
        sql0 = 'SELECT id, alert_ip, alert_time, send_time, send_to, alert_content, alert_level, item_name, item_value, send_result, send_method FROM zbx_alerts_info WHERE TO_DAYS(NOW()) - TO_DAYS(alert_time) <= "%s" order by id desc' % timed

        o = {
        'status':1,
        'table_str':'',
        'total_page':'',
        'pagation_str':'',
        'rzcount':''
        }

	sqlrz = sqlinit(sql0)   # 取出所有日期内的item
        resql = []
        for c in sqlrz: # 再次匹配，匹配出搜索字段的item，存到列表resql
		c = list(c)
		c[2] = c[2].strftime("%Y-%m-%d %H:%M:%S")
		c[3] = c[3].strftime("%Y-%m-%d %H:%M:%S")
		mondata = [j.encode("utf-8") for j in c[1:]]
                #mondata[1] = c[2].strftime("%Y-%m-%d %H:%M:%S")
                #mondata[2] = c[3].strftime("%Y-%m-%d %H:%M:%S")
                # 第二次过滤（按搜索的字段）
                if re.findall(modname,''.join(mondata)):
                        resql.append(c)
	startitem = (page - 1)*count         # 起始item（从列表resql中取的）
        if page == 1:
        	countrz = resql[0:count]
        else:
        	countrz = resql[startitem:startitem + count]
        table_html = ''
        for souitem in countrz:
                table_html = table_html + ''' <tr>
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
                                        </tr>''' % (souitem[2], souitem[1], souitem[5], souitem[7], souitem[8], souitem[3], souitem[10], souitem[4], souitem[6], souitem[9])
        o['table_str'] = table_html
        o['rzcount'] = '''<p style="font-size:20px;font-weight:bold">搜索时间：<font size="5" face="arial" color="blue">%s</font>&nbsp&nbsp 关键字：<font size="5" face="arial" color="blue">%s</font>&nbsp&nbsp 总条数：<font size="5" face="arial" color="blue">%s</font></p>''' % (timedate, modname, len(resql))

        if len(resql) % count == 0:
                o['total_page'] = len(resql)/count
        else:
                o['total_page'] = len(resql)/count + 1
        # 拼页码html
        page_html = ''
        if page > 1:    #点击的页码大于1，返回的页码有"上一页"
                page_html = page_html + '''
                                <li data-page="%s" class="page-reboot"><a href="#">上一页</a></li> ''' % (page - 1)
        if o['total_page'] <= 10:       #总页码小于等于10，返回所有的页码
                page_html = pagehtml(page_html, page, 1, o['total_page'] + 1)
        else:   #总页码大于10的，分两种情况：点击的页码大不大于6
                if page <= 6:   #点击的页码不大于6
                        page_html = pagehtml(page_html, page, 1, 11)
                else:   #点击的页码大于6，分为两种情况：总页码和点击的页码相差5以上和以下
                        if o['total_page'] > page + 5:  #总页码比点击的页码大于5
                                page_html = pagehtml(page_html, page, page - 5, page + 5)
                        else:   #总页码比点击的页码不大于5
                                page_html = pagehtml(page_html, page, page - 5, o['total_page'] + 1)

        if page < o['total_page']:      #点击的页码小于总页码数，返回的页码有"下一页"
                page_html = page_html + '''<li data-page="%s" class="page-reboot"><a href="#">下一页</a></li>''' % (page + 1)

        o['pagation_str'] = page_html
        # 返回给前端
        return json.dumps(o)


