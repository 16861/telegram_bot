# system classes import
import json, requests, sqlite3, time, re

# user classes import
import botcalendar, logger

CONFIG_NAME = "bot.conf"
BASE_URL = "http://api.telegram.org/bot"

class bot_db():
    def __init__(self):
        self.DBNAME = "botdb.sqlite3"
    def insertNewTask(self, text, expire_date, update_id, sender_id, chat_id):
        query = "INSERT INTO messages"+ \
          "(text, expire_date, update_id, sender_id, chat_id, insert_date, done, deleted)" + \
          " VALUES('{0}', '{1}', '{2}', {3}, {4}, '{5}', {6}, {7})".format( \
          text, expire_date, update_id, sender_id, chat_id, time.strftime("%Y-%m-%d %H:%M:%S"), 0, 0)
        with sqlite3.connect(self.DBNAME) as conn:
            conn.execute(query)
            conn.commit()
        print("Message with update_id: {0}, is  inserted!".format(update_id))

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
            res = conn.execute(check_query)
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


        self.TYPE_NEW_TASK = 10
        self.TYPE_SHOW_TASKS = 20
        self.TYPE_DELETE_TASK = 30
        self.TYPE_SET_TASK_DONE = 40
        self.TYPE_EXIT = 50

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
        allowed commands: add task, delete task, show tasks

        '''
        mes = " ".join(message.split()).split(' ')
        if len(mes) == 0:
            # void message is recieved
            # self._lg.writeLog(logger.WARN_LEVEL, "Recieved void message!")
            return None, None
        # if mes[0] in ["add", "delete"] and len(mes) != 3:
            # write to log
            # return None, None
        if mes[0] == "add":
            if mes[1] == "task":
                task = re.search("\"(.+)\"", message).group(1)
                expire_date = re.search("\d{2}.\d{2}.\d{2,4}", message).group(0)
                if expire_date[-3:] != '.':
                    expire_date = expire_date.replace(expire_date[-2:], "20"+expire_date[-2:])
                expire_date = expire_date[-4:] + "-" + expire_date[3:5] + "-" + expire_date[:2]
                return self.TYPE_NEW_TASK, {"task": task, "expire_date": expire_date}
        elif mes[0] == "show":
            if mes[1] == "tasks":
                if len(mes) == 3 and mes[2].isdigit():
                    res = self.db.getTasks(mes[2])
                else:
                    res = self.db.getTasks()
                return self.TYPE_SHOW_TASKS, {'tasks': res}
        elif mes[0] == "delete":
            if mes[1] == "task":
                task_id = mes[2]
                data = {}
                if not self.db.removeTask(task_id):
                    data['infos'] =  "Wrong id! No task is deleted )"
                else:
                    data['infos'] = "Delete task with id {0}".format(task_id)
                return self.TYPE_DELETE_TASK, data
        elif mes[0] == "set":
            if mes[1] == "task":
                if mes[3] == "done":
                    data = {}
                    if not self.db.setTaskDone(mes[2]):
                        data['infos'] = "Task with id {0} is done!".format(mes[2])
                    else:
                        data['infos'] = "Can't find task with id {0}".format(mes[2])
                    return self.TYPE_SET_TASK_DONE
        elif mes[0] in ["exit", "quit"]:
            self._lg.writeLog(logger.INFO_LEVEL, "Work for bot is done. Closing...")
            return self.TYPE_EXIT, None
        return None, None
    def Remind(self):
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
        not_exit_flag = True
        url = self._getUrl("get updates")
        data = self._sendCommand("GET", url)
        if data.status_code != 200:
            print(data.status_code, data.text)
            return
        js_data = json.loads(data.text)
        #print(js_data)
        if len(js_data["result"]) == 0:
            #no new messages
            return True

        #process incoming messages
        for res in js_data['result']:
            action_type, data = self.parseSenderMessage(res['message']['text'])
            if action_type == self.TYPE_NEW_TASK:
                #write message into db
                sender_id = self.db.getSenderIdByTelegramId(res['message']['from']['id'])
                chat_id = self.db.getChatIdByTelegramId(res['message']['chat']['id'])
                self.db.insertNewTask(data['task'], data['expire_date'], res['update_id'], \
              sender_id, chat_id)

                prnt = "Recieve message from: " + \
                  res["message"]["from"]["first_name"] + " " + \
                  ". Task is added! )"
                self.SendMessage(prnt)
            elif action_type == self.TYPE_SHOW_TASKS:
                #show tasks, all or by specified limit parameter
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
                not_exit_flag = False

        # writing new config into file with incremented and updated update_id
        with open(CONFIG_NAME, 'w') as fd:
            print(True)
            if self.config['last_updates'] <= max([mes["update_id"] for mes in js_data["result"]]):
                self.config['last_updates'] = \
                 max([mes["update_id"] for mes in js_data["result"]])+1
            self.config['last_updates'] = \
              max([mes["update_id"] for mes in js_data["result"]])+1
            fd.write(str(self.config).replace("'", "\""))
        return not_exit_flag

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
    def SleepFor(self, sec=5):
        '''
        sleeping for seconds defined in sec variable
        '''
        time.sleep(sec)