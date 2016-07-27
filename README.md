
#概述
xinop 是一个基于 Flask 跟 Bootstrap 开发的 运维管理系统 ，包含了资源管理(CMDB)系统及其它运维工具。
#功能
1. CMDB设备添加，删除，修改。实现基于IDC→机柜→设备包含关系的浏览方式，服务器网卡与所连交换机端口的连接关系，主机分类显示。
2. 实现对设备的搜索功能，支持任意字段的搜索结果匹配，支持对搜索的结果导出成Excel文件。
3. 实现设备的页面编辑提交，也支持编辑到Excel文件做批量上传。
4. 实现实时显示代码上线的结果，具体到每台机器及上线的文件。
5. 实现Zabbix告警结果的显示，多平台CDN流量的实时显示。
6. 实现Saltstack web ui，对登录用户的Saltstack使用权限做二次限制，操作审计功能，危险命令过滤功能。

#xinopha还在持续开发完善阶段，有问题欢迎交流 
我的邮箱: chenkun1998@163.com

#相关预览
![IDC](https://github.com/chenkun1998/xinop/blob/master/showpics/idc.png)
![分类主机](https://github.com/chenkun1998/xinop/blob/master/showpics/hosts.png)
![批量导入](https://github.com/chenkun1998/xinop/blob/master/showpics/auto.png)
![网络设备添加](https://github.com/chenkun1998/xinop/blob/master/showpics/addnets.png)
![上线实时结果](https://github.com/chenkun1998/xinop/blob/master/showpics/update.jpg)
![Saltstack ui](https://github.com/chenkun1998/xinop/blob/master/showpics/cmd.png)
![Zabbix结果查询](https://github.com/chenkun1998/xinop/blob/master/showpics/zabbix.png)


