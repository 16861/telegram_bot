import json, time, requests, re


import logger, botcalendar, sql3_bot, tasks

CONFIG_NAME = "bot.conf"
BASE_URL = "http://api.telegram.org/bot"
HABRAHABR_MAIN = "https://habrahabr.ru/"

class TelegramBot():
    def __init__(self):
        self.config = {}
        self.db = sql3_bot.BotDB()
        self.calendar = botcalendar.BotCalendar(time.strftime("%d"), \
          time.strftime("%m"), time.strftime("%y"))
        self._lg = logger.Logger()
        self.task = tasks.Task()
        self.habr_newses = {}


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
        self.TYPE_SAY_HELLO = 110
        self.TYPE_HABR_SHOW_NEWSES = 120
        self.TYPE_HABR_GET_LINK = 130

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
        if mes == "hello bot":
            return self.TYPE_SAY_HELLO, None

        #when action is not edn aand expectict further data from user
        if self.ACTION_EDIT_TASK_ID:
            if len(mes) < 2:
                return self.TYPE_ERROR, None
            if mes[0] == "text":
                new_text = re.search("\"(.+)\"", message).group(1)
                self.db.execute_script(self.task.updeteTaskQuery(self.ACTION_EDIT_TASK_ID, new_text, 'text'))
                self.ACTION_EDIT_TASK_ID = None
            elif mes[0] == "date":
                new_date = re.search("\d{2}.\d{2}.\d{2,4}", message).group(0)
                if new_date[-3:] != '.':
                    new_date = new_date[:-2] + "20" + new_date[-2:]
                new_date = new_date[-4:] + "-" + new_date[3:5] + "-" + new_date[:2]
                self.db.execute_script(self.task.updeteTaskQuery(self.ACTION_EDIT_TASK_ID, new_date, 'date'))
                self.ACTION_EDIT_TASK_ID = None
            return self.TYPE_TASK_CHANGED, None

        #main loop, check entered commands
        #there is next command: add, show, delete, set, exit,
        # bot(block of command for manage bot), edit, help(in plans:) )
        if mes[0] == "add":
            if len(mes) < 2:
                return self.TYPE_ERROR, None
            if mes[1] == "task":
                new_task = re.search("\"(.+)\"", message).group(1)
                expire_date = re.search("\d{2}.\d{2}.\d{2,4}", message).group(0)
                if expire_date[-3:] != '.':
                    expire_date = expire_date[:-2] + "20" + expire_date[-2:]
                expire_date = expire_date[-4:] + "-" + expire_date[3:5] + "-" + expire_date[:2]
                return self.TYPE_NEW_TASK, {"task": new_task, "expire_date": expire_date}
            
        # show tasks either all or determined amount
        elif mes[0] == "show":
            if len(mes) < 2:
                return self.TYPE_ERROR, None
            if mes[1] == "tasks":
                if len(mes) == 3 and mes[2].isdigit():
                    res = self.db.execute_script(self.task.getTasksQuery(mes[2]))
                else:
                    res = self.db.execute_script(self.task.getTasksQuery())
                return self.TYPE_SHOW_TASKS, {'tasks': res}
        #delete task
        elif mes[0] == "delete":
            if len(mes) < 4:
                return self.TYPE_ERROR, None
            if mes[1] == "task" and mes[2] == "with" and mes[3] == "id":
                task_id = mes[4]
                data = {}
                [check_query, update_query] = self.task.removeTaskQuery(task_id)
                if not self.db.execute_script(check_query):
                    data['infos'] = "Wrong id! No task is deleted )"
                else:
                    self.db.execute_script(update_query)
                    data['infos'] = "Delete task with id {0}".format(task_id)
                return self.TYPE_DELETE_TASK, data
        elif mes[0] == "update":
            if len(mes) < 4:
                return self.TYPE_ERROR, None
            if mes[1] == "task" and mes[2] == "with" and mes[3] == "id":
                if mes[4] == "set" and mes[5] == 'done':
                    data = {}
                    if not self.db.execute_script(self.task.setTaskDoneQuery(mes[2])):
                        data['infos'] = "Task with id {0} is completed!".format(mes[2])
                    else:
                        data['infos'] = "Can't find task with id {0}".format(mes[2])
                    return self.TYPE_SET_TASK_DONE, data
                if mes[4].isdigit:
                    if self.db.execute_script(self.task.checkTaskIdQuery(mes[4])):
                        self.ACTION_EDIT_TASK_ID = mes[4]
                        return self.TYPE_EDIT_TASK, None
                    else:
                        self.SendMessage("No such task found!")
        elif mes[0] == "habr":
            if len(mes) < 2:
                return self.TYPE_ERROR, None
            if mes[1] == "show":
                site = requests.get(HABRAHABR_MAIN)
                news_temp = re.findall("<a.+?href=\"(https://habrahabr.ru/post/[0-9]+?/)\".*?>(.*?)</a>", site.text)
                self.habr_newses = []
                indx = 1
                data = ""
                for link, text in news_temp:
                    self.habr_newses.append({"index": indx, "title": text, "link":link})
                    indx += 1
                if len(mes) == 3 and mes[2].isdigit() and 1 < int(mes[2]) < indx:
                    indx = int(mes[2])
                for news in self.habr_newses:
                    data += str(news["index"]) + ", " + news['title'] + "\n"
                    if news["index"] >= indx:
                        break
                return self.TYPE_HABR_SHOW_NEWSES, data
            elif mes[1] == "link":
                if len(mes) < 3:
                    return self.TYPE_ERROR, None
                print([news['index'] for news in self.habr_newses])
                if self.habr_newses and int(mes[2]) in [news['index'] for news in self.habr_newses]:
                    return self.TYPE_HABR_GET_LINK, "Link: {0}".format([news['link'] for news in self.habr_newses if news['index'] == int(mes[2])][0])
                else:
                    self.SendMessage("No news found!")
        elif mes[0] == "bot":
            if len(mes) < 2:
                return self.TYPE_ERROR, None
            if mes[1] == "update":
                return self.TYPE_UPDATE_BOT, None
            elif mes[1] == "restart":
                return self.TYPE_RESTART_BOT, None
            elif mes[1] == "exit":
                return self.TYPE_EXIT, None
        return None, None
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
            running_bot = False
            return running_bot
        js_data = json.loads(data.text)
        if len(js_data["result"]) == 0:
            #no new messages
            return running_bot

        #process incoming message        print("Trye")
        user_id = int(self.getValidUserId())
        #there ara two types of message: "message" and "edited_message"
        type_of_message = ""
        for res in js_data['result']:
            for key in res.keys():
                if key != "update_id":
                    type_of_message = key
            if user_id != res[type_of_message]["from"]["id"]:
                continue
            action_type, data = self.parseSenderMessage(res[type_of_message]['text'].lower())
            if action_type == self.TYPE_NEW_TASK:
                #write message into db
                sender_id = self.getSenderIdByTelegramId(res[type_of_message]['from']['id'])
                chat_id = self.getChatIdByTelegramId(res[type_of_message]['chat']['id'])
                result = self.db.execute_script(self.task.insertNewTaskQuery(data['task'], data['expire_date'], res['update_id'], \
              sender_id, chat_id))
                self._lg.writeLog(logger.INFO_LEVEL, "Write to db: " + str(result))

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
            elif action_type == self.TYPE_HABR_SHOW_NEWSES or action_type == self.TYPE_HABR_GET_LINK:
                self.SendMessage(data)
        # writing new config into file with incremented and updated update_id
        with open(CONFIG_NAME, 'w') as fd:
            if self.config['last_updates'] <= max([mes["update_id"] for mes in js_data["result"]]):
                self.config['last_updates'] = \
                 max([mes["update_id"] for mes in js_data["result"]])+1
            self.config['last_updates'] = \
              max([mes["update_id"] for mes in js_data["result"]])+1
            fd.write(str(self.config).replace("'", "\"").replace("False","false").replace("True","true"))
        return running_bot

    def getValidUserId(self):
        query = "SELECT id_user FROM senders WHERE first_name = 'Igor' and last_name = 'Kuzmenko'"
        res = self.db.execute_script(query)
        if len(res) == 0:
            return None
        else:
            return res[0][0]
    def getChatIdByTelegramId(self, id):
        query = "SELECT id FROM chats where chat_id={0}".format(id)
        res = self.db.execute_script(query)
        if len(res) == 0:
            return None
        else:
            return res[0][0]
    def getSenderIdByTelegramId(self, id):
        query = "SELECT id FROM senders where id_user={0}".format(id)
        res = self.db.execute_script(query)
        if len(res) == 0:
            return None
        else:
            return res[0][0]
    def SleepFor(self, sec=3):
        '''
        sleeping for seconds defined in sec variable
        '''
        time.sleep(sec)