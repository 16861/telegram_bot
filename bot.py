# system classes import
import json, requests, sqlite3, time, re, os

# user classes import
import botcalendar, logger, db_scripts

CONFIG_NAME = "bot.conf"
BASE_URL = "http://api.telegram.org/bot"

class bot_db():
    def __init__(self):
        self.DBNAME = "botdb.sqlite3"
        self.initDB()
    def initDB(self):
        if os.path.exists(self.DBNAME):
            return
        with sqlite3.connect(self.DBNAME) as conn:
            conn.execute(db_scripts.CREATE_CHATS)
            conn.execute(db_scripts.CREATE_SENDERS)
            conn.execute(db_scripts.CREATE_MESSAGES)

            conn.execute(db_scripts.INSERT_INTO_CHATS)
            conn.execute(db_scripts.INSERT_INTO_SENDERS)
            conn.commit() 
    def insertNewTask(self, text, expire_date, update_id, sender_id, chat_id):
        query = "INSERT INTO messages"+ \
          "(text, expire_date, update_id, sender_id, chat_id, insert_date, done, deleted)" + \
          " VALUES('{0}', '{1}', '{2}', {3}, {4}, '{5}', {6}, {7})".format( \
          text, expire_date, update_id, sender_id, chat_id, time.strftime("%Y-%m-%d %H:%M:%S"), 0, 0)
        with sqlite3.connect(self.DBNAME) as conn:
            conn.execute(query)
            conn.commit()
        return "Message with update_id: {0}, is  inserted!".format(update_id)

    def getSendersIds(self):
        query = "SELECT id FROM senders"
        ids = []
        with sqlite3.connect(self.DBNAME) as conn:
            for sender_id in conn.execute(query):
                ids.append(sender_id[0])
        return ids
    def getChatIds(self):
        query = "SELECT id FROM chats"
        ids = []
        with sqlite3.connect(self.DBNAME) as conn:
            for chat_id in conn.execute(query):
                ids.append(chat_id[0])
        return ids

    def getChatIdByTelegramId(self, id):
        query = "SELECT id FROM chats where chat_id={0}".format(id)
        with sqlite3.connect(self.DBNAME) as conn:
            res = conn.execute(query).fetchall()
            if len(res) == 0:
                return None
            else:
                return res[0][0]
    def getSenderIdByTelegramId(self, id):
        query = "SELECT id FROM senders where id_user={0}".format(id)
        with sqlite3.connect(self.DBNAME) as conn:
            res = conn.execute(query).fetchall()
            if len(res) == 0:
                return None
            else:
                return res[0][0]
    def getTasks(self, limit=None):
        '''
        if limit == None return all tasks
        '''
        if not limit:
            query = "SELECT id, text, expire_date FROM messages WHERE deleted = 0 ORDER BY expire_date"
        else:
            query = "SELECT id, text, expire_date FROM messages WHERE deleted = 0 ORDER BY expire_date LIMIT {0}".format(limit)
        with sqlite3.connect(self.DBNAME) as conn:
            res = conn.execute(query).fetchall()
            if len(res) == 0:
                return None
            else:
                return res
    def removeTask(self, id):
        '''
        removing task from db. row is not completely deleted 
        but field deleted changed to 1
        '''
        update_query = "UPDATE messages SET deleted = 1 WHERE id = {0}".format(id)
        check_query = "SELECT id FROM messages WHERE id = {0}".format(id)
        with sqlite3.connect(self.DBNAME) as conn:
            res = conn.execute(check_query).fetchall()
            if len(res) == 0:
                return False
            conn.execute(update_query)
        return True
    def setTaskDone(self, id):
        '''
        mark task as complete
        '''
        update_query = "UPDATE messages SET done = 1 WHERE id = {0}".format(id)
        check_query = "SELECT id FROM messages WHERE id = {0}".format(id)
        with sqlite3.connect(self.DBNAME) as conn:
            res = conn.execute(check_query)
            if len(res) == 0:
                return False
            conn.execute(update_query)
        return True
    def getTaskForPeriod(self, start_date, end_date):
        query = "SELECT id, text, expire_date FROM messages WHERE expire_date \
          BETWEEN '{0}' AND '{1}' ORDER BY expire_date".format(start_date, end_date)
        print(query)
        with sqlite3.connect(self.DBNAME) as conn:
            res = conn.execute(query).fetchall()
            if len(res) == 0:
                return None
            else:
                return res
    def getValidUserId(self):
        query = "SELECT id_user FROM senders WHERE first_name = 'Igor' and last_name = 'Kuzmenko'"
        with sqlite3.connect(self.DBNAME) as conn:
            res = conn.execute(query).fetchall()
            if len(res) == 0:
                return None
            else:
                return res[0][0]
    def checkTaskId(self, id):
        query = "SELECT id FROM messages WHERE id = {0}".format(id)
        with sqlite3.connect(self.DBNAME) as conn:
            res = conn.execute(query).fetchall()
            if res:
                return True
            else:
                return False
    def updeteTaskText(self, id, new_text):
        query = "UPDATE messages SET text = '{1}' WHERE id = {0}".format(id, new_text)
        with sqlite3.connect(self.DBNAME) as conn:
            conn.execute(query)
    def updeteTaskExpireDate(self, id, new_date):
        query = "UPDATE messages SET expire_date = '{1)' WHERE id = {0}".format(id, new_date)
        with sqlite3.connect(self.DBNAME) as conn:
            conn.execute(query)
class TelegramBot():
    '''
    telegram bot class
    '''
    def __init__(self):
        self.config = {}
        with open(CONFIG_NAME, 'r') as fd:
            self.config = json.loads(fd.read())
        self.db = bot_db()
        self.calendar = botcalendar.BotCalendar(time.strftime("%d"), \
          time.strftime("%m"), time.strftime("%y"))
        self._lg = logger.Logger()


        self.ACTION_EDIT_TASK_ID = None

        self.TYPE_ERROR = 0
        self.TYPE_NEW_TASK = 10
        self.TYPE_SHOW_TASKS = 20
        self.TYPE_DELETE_TASK = 30
        self.TYPE_SET_TASK_DONE = 40
        self.TYPE_EXIT = 50
        self.TYPE_UPDATE_BOT = 60
        self.TYPE_RESTART_BOT = 70
        self.TYPE_TASK_CHANGED = 80
        self.TYPE_EDIT_TASK = 90
        self.TYPE_TASK_CHANGED = 100

        self.RestartBotFlag = False
        self.UpdateBotFlag = False

        self._lg.writeLog(logger.INFO_LEVEL, "Bot is ready to work....")
    def _getUrl(self, command=None):
        '''
        get url for sending to telegram server
        '''
        if not command:
            return BASE_URL + self.config['token']
        if command == "send message":
            return  BASE_URL + \
              self.config['token'] + \
              "/sendMessage?chat_id={0}&text=".format(self.config['chat_id'])
        elif command == "get updates":
            return BASE_URL + \
              self.config['token'] + \
              "/getUpdates?offset=" + str(self.config['last_updates'])
        return None
    def _sendCommand(self, method, url, headers=None, data=None):
        '''
        sending command to chat using POST or GET methods
        '''
        if method == "GET":
            resp = requests.get(url, headers=headers, data=data)
            return resp
        elif method == "POST":
            resp = requests.post(url, headers=headers, data=data)
            return resp
    def parseSenderMessage(self, message):
        '''
        parsing recieved mesage from chat participants
        allowed commands: add task, delete task, show tasks, bot(block of command for manage bot)
        edit, exit, set, help(in plans:)
        '''
        mes = " ".join(message.split()).split(' ')
        if len(mes) == 0:
            # void message is recieved
            if self.ACTION_EDIT_TASK_ID:
                self.SendMessage("Can't edit task, please specify parameters")
                self.ACTION_EDIT_TASK_ID = None
            return None, None

        #when action is not edn aand expectict further data from user
        if self.ACTION_EDIT_TASK_ID:
            if len(mes) < 2:
                return self.TYPE_ERROR, None
            if mes[0] == "text":
                new_text = re.search("\"(.+)\"", message).group(1)
                self.db.updeteTaskText(self.ACTION_EDIT_TASK_ID, new_text)
                self.ACTION_EDIT_TASK_ID = None
            elif mes[0] == "date":
                new_date = message.search("\d{2}.\d{2}.\d{2,4}", message).group(0)
                if new_date[-3:] != '.':
                    new_date = new_date[:-2] + "20" + new_date[-2:]
                new_date = new_date[-4:] + "-" + new_date[3:5] + "-" + new_date[:2]
                self.db.updeteTaskExpireDate(self.ACTION_EDIT_TASK_ID, new_date)
                self.ACTION_EDIT_TASK_ID = None
            return self.TYPE_TASK_CHANGED, None

        #main loop, check entered commands
        #there is next command: add, show, delete, set, exit,
        # bot(block of command for manage bot), edit, help(in plans:) )
        if mes[0] == "add":
            if len(mes) < 2:
                return self.TYPE_ERROR, None
            if mes[1] == "task":
                task = re.search("\"(.+)\"", message).group(1)
                expire_date = re.search("\d{2}.\d{2}.\d{2,4}", message).group(0)
                if expire_date[-3:] != '.':
                    expire_date = expire_date[:-2] + "20" + expire_date[-2:]
                expire_date = expire_date[-4:] + "-" + expire_date[3:5] + "-" + expire_date[:2]
                return self.TYPE_NEW_TASK, {"task": task, "expire_date": expire_date}
        # show tasks either all or determined amount
        elif mes[0] == "show":
            if len(mes) < 2:
                return self.TYPE_ERROR, None
            if mes[1] == "tasks":
                if len(mes) == 3 and mes[2].isdigit():
                    res = self.db.getTasks(mes[2])
                else:
                    res = self.db.getTasks()
                return self.TYPE_SHOW_TASKS, {'tasks': res}
        elif mes[0] == "delete":
            if len(mes) < 4:
                return self.TYPE_ERROR, None
            if mes[1] == "task" and mes[2] == "with" and mes[3] == "id":
                task_id = mes[4]
                data = {}
                if not self.db.removeTask(task_id):
                    data['infos'] = "Wrong id! No task is deleted )"
                else:
                    data['infos'] = "Delete task with id {0}".format(task_id)
                return self.TYPE_DELETE_TASK, data
        elif mes[0] == "set":
            if len(mes) < 4:
                return self.TYPE_ERROR, None
            if mes[1] == "task":
                if mes[3] == "done":
                    data = {}
                    if not self.db.setTaskDone(mes[2]):
                        data['infos'] = "Task with id {0} is done!".format(mes[2])
                    else:
                        data['infos'] = "Can't find task with id {0}".format(mes[2])
                    return self.TYPE_SET_TASK_DONE, data
        elif mes[0] in ["exit", "quit"]:
            self._lg.writeLog(logger.INFO_LEVEL, "Work for bot is done. Closing...")
            return self.TYPE_EXIT, None
        elif mes[0] == "bot":
            if len(mes) < 2:
                return self.TYPE_ERROR, None
            if mes[1] == "update":
                return self.TYPE_UPDATE_BOT, None
            elif mes[1] == "restart":
                return self.TYPE_RESTART_BOT, None
        elif mes[0] == "edit":
            if len(mes) < 5:
                return self.TYPE_ERROR, None
            if mes[1] == "task":
                if mes[2] == "with" and mes[3] == "id":
                    if self.db.checkTaskId(mes[4]):
                        self.ACTION_EDIT_TASK_ID = mes[4]
                        return self.TYPE_EDIT_TASK, None
                    else:
                        self.SendMessage("No such task in db!")
        return None, None
    def Remind(self):
        '''
        reminder currently in develepment need to add some basic functionality
        '''
        current_data = time.strftime("%Y-%m-%d")
        current_time = time.strftime("%H%M")
        if current_time[:2] == "23":
            to_date = "2017-" + self.calendar.getData(7)
            print("To date: ", to_date)
            messege_to_chat = "You have next tasks ahead:\n"
            for task in self.db.getTaskForPeriod(current_data, to_date):
                messege_to_chat += task[1] + ", id: " + str(task[0]) + \
                  ", expires " + task[2] + "\n"
            self.SendMessage(messege_to_chat)
    def GetUpdates(self):
        '''
        get new updates, update updete_id in config, insert messages into db
        '''
        #get messages from Telegram API
        running_bot = True
        with open(CONFIG_NAME, 'r') as fd:
            self.config = json.loads(fd.read())
        url = self._getUrl("get updates")
        data = self._sendCommand("GET", url)
        if data.status_code != 200:
            print(data.status_code, data.text)
            return
        js_data = json.loads(data.text)
        if len(js_data["result"]) == 0 or not running_bot:
            #no new messages
            return running_bot
        
       
        #process incoming message
        user_id = int(self.db.getValidUserId())
        type_of_message = ""
        for res in js_data['result']:
            for key in res.keys():
                if key != "update_id":
                    type_of_message = key
            if user_id != res[type_of_message]['from']['id']:
                continue
            action_type, data = self.parseSenderMessage(res[type_of_message]['text'].lower())
            if action_type == self.TYPE_NEW_TASK:
                #write message into db
                sender_id = self.db.getSenderIdByTelegramId(res[type_of_message]['from']['id'])
                chat_id = self.db.getChatIdByTelegramId(res[type_of_message]['chat']['id'])
                result = self.db.insertNewTask(data['task'], data['expire_date'], res['update_id'], \
              sender_id, chat_id)
                self._lg.writeLog(logger.INFO_LEVEL, result)

                prnt = "Recieve message from: " + \
                  res[type_of_message]["from"]["first_name"] + " " + \
                  ". Task is added! )"
                self.SendMessage(prnt)
            elif action_type == self.TYPE_SHOW_TASKS:
                #show tasks, all or by specified limit parameter
                if not data["tasks"]:
                    prnt = "There are no tasks!"
                else:
                    prnt = "There are next tasks:\n"
                    for task in data['tasks']:
                        prnt += task[1] + ", id: " + str(task[0]) + ", expire: " + str(task[2]) + "\n"
                self.SendMessage(prnt)
            elif action_type == self.TYPE_DELETE_TASK:
                # delete specific task
                self.SendMessage(data['infos'])
            elif action_type == self.TYPE_SET_TASK_DONE:
                # mark some task(by id) as complete
                self.SendMessage(data['infos'])
            elif action_type == self.TYPE_EXIT:
                # exit from bot
                self.SendMessage("Bot is down!")
                running_bot = False
            elif action_type == self.TYPE_UPDATE_BOT:
                self.UpdateBotFlag = True
                self.SendMessage("Updating bot...")
                running_bot = False
            elif action_type == self.TYPE_RESTART_BOT:
                self.RestartBotFlag = True
                self.SendMessage("Restarting bot...")
                running_bot = False
            elif action_type == self.TYPE_EDIT_TASK:
                self.SendMessage("Enter new text or expire date(exaple text 'new text'):")
            elif action_type == self.TYPE_TASK_CHANGED:
                self.SendMessage("Successfully change task! Enter 'show tasks' to see other tasks :)")
            elif action_type == self.TYPE_ERROR:
                self.SendMessage("Wrong command. I don'n now what to do!")

        # writing new config into file with incremented and updated update_id
        with open(CONFIG_NAME, 'w') as fd:
            if self.config['last_updates'] <= max([mes["update_id"] for mes in js_data["result"]]):
                self.config['last_updates'] = \
                 max([mes["update_id"] for mes in js_data["result"]])+1
            self.config['last_updates'] = \
              max([mes["update_id"] for mes in js_data["result"]])+1
            fd.write(str(self.config).replace("'", "\"").replace("False","false").replace("True","true"))
        return running_bot
    def SendMessage(self, message):
        '''
        send message to chat
        '''
        url = self._getUrl("send message")
        resp = self._sendCommand("GET", url+message)
        if resp.status_code == 200:
            print("OK, message is send")
        else:
            print("Message is not send!")
            print(resp.status_code, resp.text)
    def SleepFor(self, sec=3):
        '''
        sleeping for seconds defined in sec variable
        '''
        time.sleep(sec)