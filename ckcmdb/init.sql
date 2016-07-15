
create database xinop character set utf8;

use xinop;

Create table hosts(
	id int not null auto_increment primary key,
	hrack varchar(30),
        hsite varchar(5),
	devstyle varchar(20),
	usize varchar(10),
	cpunum varchar(3),
	memnum varchar(2),
	memsize varchar(6),
	disk varchar(2),
	disksize varchar(5),
	diskgt varchar(2),
	raid varchar(10),
	insidecard varchar(20),
	insideip varchar(20),
	insidesw varchar(60),
	iport varchar(10),
	ivlan varchar(10),
	outsidecard varchar(20),
	outsideip varchar(20),
	outsidesw varchar(60),
	oport varchar(10),
	ovlan varchar(10),
	mngcard varchar(20),
	mngip varchar(20),
	mngsw varchar(60),
	mngport varchar(10),
	mngvlan varchar(10),
	devicetype varchar(10),
	osversion varchar(20),
	busstyle varchar(20),
	codeenv varchar(5),
	assetnumber varchar(30),
	owner varchar(10),
	runstatus varchar(8),
	remarks varchar(200),
	sitecode varchar(5)
);

Create table idcs(
        id int not null auto_increment primary key,
        idcname varchar(200),
        racksnum int(5),
        hostsnum int(5),
        idcipinfo varchar(200),
	idcaddr varchar(200),
	idccontacts varchar(200),
	idcphone varchar(200),
	idcnote varchar(200)
);

Create table racks(
        id int not null auto_increment primary key,
	hostsnum int(2),
        rackname varchar(200),
	idcname varchar(200),
        rackassetlabel varchar(200),
	rackaddr varchar(200),
        racksize varchar(200),
        racknote varchar(200)
);

Create table netdevices(
        id int not null auto_increment primary key,
	ndrack varchar(200),
	ndaddr varchar(200),
        ndname varchar(200),
        ndstyle varchar(200),
        ndassetlabel varchar(200),
        linkdevicetype varchar(200),
	linkdeviceassetnumber varchar(200),
	ndnote varchar(200),
	devicetype varchar(20),
	owner varchar(10),
	runstatus varchar(10)
);

Create table ndports(
        id int not null auto_increment primary key,
        ndname varchar(200),
        ndport varchar(20),
        ndvlan varchar(10),
	ndipaddr varchar(20),
        ndlinknd varchar(30),
	linkndport varchar(20),
	linkndipaddr varchar(20)
);

Create table vms(
        id int not null auto_increment primary key,     
        devicetype varchar(10),
	vmhostip varchar(20),
        serstyle varchar(20),
        busstyle varchar(20),
	cpunum varchar(3),
	memsize varchar(2),
	disk varchar(2),
	disksize varchar(5),
	diskgt varchar(2),
	insidecard varchar(20),
	insideip varchar(20),
        codeenv varchar(5),
        owner varchar(10),
        runstatus varchar(8),
        remarks varchar(200)
);

alter table hosts convert to character set utf8;
alter table idcs convert to character set utf8;
alter table racks convert to character set utf8;
alter table vhosts convert to character set utf8;

