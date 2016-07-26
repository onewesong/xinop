
create table cmdhistory(
        id int not null auto_increment primary key,
	cmdtime bigint(11),
	username varchar(200),
        cmdname varchar(200),
        cmdhost varchar(200)
);

