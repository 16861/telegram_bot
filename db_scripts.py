# scripts for creating db

#first need to create and chats and senders
CREATE_CHATS = '''
CREATE TABLE `chats` (
	`id`	INTEGER PRIMARY KEY AUTOINCREMENT,
	`chat_id`	TEXT NOT NULL,
	`type`	TEXT NOT NULL,
	`sender_id`	INTEGER NOT NULL,
	FOREIGN KEY(`sender_id`) REFERENCES senders ( id )
);
'''

CREATE_SENDERS = '''
CREATE TABLE `senders` (
	`id`	INTEGER PRIMARY KEY AUTOINCREMENT,
	`first_name`	TEXT NOT NULL,
	`last_name`	TEXT NOT NULL,
	`id_user`	TEXT NOT NULL
);
'''

#then creating messaging
CREATE_MESSAGES = '''
CREATE TABLE `messages` (
	`id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	`text`	TEXT NOT NULL,
	`update_id`	TEXT NOT NULL UNIQUE,
	`sender_id`	INTEGER NOT NULL,
	`chat_id`	INTEGER NOT NULL,
	`insert_date`	TEXT,
	`expire_date`	TEXT,
	`type`	INTEGER,
	`done`	INTEGER,
	`deleted`	INTEGER,
	FOREIGN KEY(`sender_id`) REFERENCES senders ( id ),
	FOREIGN KEY(`chat_id`) REFERENCES chats ( id )
);
'''

#inserting chats and senders data
INSERT_INTO_CHATS = '''
INSERT INTO `chats`(`chat_id`,`type`,`sender_id`) VALUES ('418486546','ptivate',1);
'''
INSERT_INTO_SENDERS = '''
INSERT INTO `senders`(`first_name`,`last_name`,`id_user`) VALUES ('Igor','Kuzmenko','418486546');
'''

