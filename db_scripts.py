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

CREATE_MESSAGE_TYPES = '''
CREATE TABLE `messgae_types` (
	`id`	INTEGER,
	`type`	TEXT NOT NULL,
	PRIMARY KEY(id)
);
'''

CREATE_BOOKMARKS = '''
CREATE TABLE `bookmarks` (
	`id`	INTEGER,
	`url`	INTEGER NOT NULL,
	`description`	TEXT,
	`rate`	INTEGER,
	`iduser`	INTEGER NOT NULL,
	`comments` TEXT,
	PRIMARY KEY(id),
	FOREIGN KEY(`iduser`) REFERENCES senders ( id )
);
'''

CREATE_TAGS = '''
CREATE TABLE `tags` (
	`id`	INTEGER,
	`name`	TEXT NOT NULL UNIQUE,
	`comments`	TEXT,
	PRIMARY KEY(id)
);
'''

CREATE_TAGS_TO_BOOKMARKS = '''
CREATE TABLE `tags_to_bookmarks` (
	`tag`	INTEGER NOT NULL,
	`bookmark`	INTEGER NOT NULL,
	FOREIGN KEY(`tag`) REFERENCES tags ( id ),
	FOREIGN KEY(`bookmark`) REFERENCES bookmarks ( id )
);
'''

#then creating messaging
CREATE_MESSAGES = '''
CREATE TABLE `messages` (
	`id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	`text`	TEXT NOT NULL,
	`update_id`	TEXT NOT NULL,
	`sender_id`	INTEGER NOT NULL,
	`chat_id`	INTEGER NOT NULL,
	`insert_date`	TEXT,
	`expire_date`	TEXT,
	`type`	INTEGER,
	`done`	INTEGER,
	`deleted`	INTEGER,
	FOREIGN KEY(`sender_id`) REFERENCES senders ( id ),
	FOREIGN KEY(`chat_id`) REFERENCES chats ( id ),
	FOREIGN KEY(`type`) REFERENCES message_types ( id )
);
'''
CREATE_REMINDERS = '''
CREATE TABLE `reminders` (
	`id`	INTEGER,
	`name`	TEXT NOT NULL,
	`time_`	TEXT NOT NULL,
	`count_`	INTEGER NOT NULL DEFAULT -1,
	PRIMARY KEY(id)
);
'''

#triggers
TRIGGER_BOOKMARKS_INSERT_1 = '''
CREATE TRIGGER insert_bookmarks_description AFTER INSERT ON bookmarks
WHEN NEW.description = ''
BEGIN
   UPDATE bookmarks set description = NULL where id = NEW.id;
 END;
'''

TRIGGER_BOOKMARKS_INSERT_2 =  '''
CREATE TRIGGER insert_bookmarks_rate AFTER INSERT ON bookmarks
WHEN NEW.rate = 0
BEGIN
   UPDATE bookmarks set rate = NULL where id = NEW.id;
 END;
'''

TRIGGER_BOOKMARKS_INSERT_3 = '''
CREATE TRIGGER insert_bookmarks_iduser AFTER INSERT ON bookmarks
WHEN NEW.iduser = 0
BEGIN
  UPDATE bookmarks SET iduser = 1 WHERE id = NEW.id;
END;
'''

TRIGGER_BOOKMARKS_INSERT_4 = '''
CREATE TRIGGER insert_bookmarks_comments AFTER INSERT ON bookmarks
WHEN NEW.comments = ''
BEGIN
  UPDATE bookmarks SET comments = NULL WHERE id = NEW.id;
END;
'''


TRIGGER_REMINDER_INSERT = '''
CREATE TRIGGER insert_reminders_iduser AFTER INSERT ON reminders
WHEN (NEW.userid is NULL)
BEGIN
  UPDATE reminders SET userid = (SELECT senders.id FROM senders WHERE id_user = '418486546') WHERE id = NEW.id;
END;
'''


#inserting chats and senders data
INSERT_INTO_CHATS = '''
INSERT INTO `chats`(`chat_id`,`type`,`sender_id`) VALUES ('418486546','ptivate',1);
'''
INSERT_INTO_SENDERS = '''
INSERT INTO `senders`(`first_name`,`last_name`,`id_user`) VALUES ('Igor','Kuzmenko','418486546');
'''

#exported variable contains, all scripts. just add new one here and on initilization of db it will be executed
#order matters!!!
ALL_SCRIPTS = [CREATE_CHATS, CREATE_SENDERS, CREATE_MESSAGE_TYPES, \
   CREATE_BOOKMARKS, CREATE_TAGS, CREATE_TAGS_TO_BOOKMARKS, CREATE_MESSAGES, \
   CREATE_REMINDERS, TRIGGER_BOOKMARKS_INSERT_1, TRIGGER_BOOKMARKS_INSERT_2, \
   TRIGGER_BOOKMARKS_INSERT_3, TRIGGER_BOOKMARKS_INSERT_4, INSERT_INTO_CHATS, INSERT_INTO_SENDERS]
