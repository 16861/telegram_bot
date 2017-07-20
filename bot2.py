import json, time, requests, re, base64
from bs4 import BeautifulSoup as BS


import logger, botcalendar, sql3_bot, tasks, bookmarks, reminder

CONFIG_NAME = "bot.conf"
BASE_URL = "http://api.telegram.org/bot"
HABRAHABR_MAIN = "https://habrahabr.ru/"

class TelegramBot():
    def __init__(self):
        with open(CONFIG_NAME, 'r') as fd:
            self.config = json.loads(fd.read())
        self.db = sql3_bot.BotDB()
        self.calendar = botcalendar.BotCalendar(time.strftime("%d"), \
          time.strftime("%m"), time.strftime("%y"))
        self._lg = logger.Logger()
        self.task = tasks.Task()
        self.bookmark = bookmarks.Bookmark()
        self.reminder= reminder.Reminder()
        self.habr_newses = {}
        self.one_minute_remind = time.strftime("%H:%M")


        self.ACTION_EDIT_TASK_ID = None
        self.ACTION_EDIT_BOOKMARK_ID = None

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
        self.TYPE_HABR = 120
        self.TYPE_BOOKMARKS = 130
        self.TYPE_REMINDERS = 140

        self.RestartBotFlag = False
        self.UpdateBotFlag = False

        self._lg.writeLog(logger.INFO_LEVEL, "Bot is ready to work....")

    def _b64decenc(self, string, encode=True):
        '''
        function for decodng and encoding inserted into db string
        if encode == True return encoded string
        perform b64decode otherwise
        '''
        if encode:
            return base64.b64encode(bytes(string, "utf-8")).decode("utf-8")
        else:
            return base64.b64decode(string).decode("utf-8")
    def _getUrl(self, command=None, iduser=None):
        '''
        get url for sending to telegram server
        '''
        if not command:
            return BASE_URL + self.config['token']
        if command == "send message":
            if not iduser:
                chat_id = self.config['chat_id']
            else:
                chat_id = iduser
            return  BASE_URL + \
              self.config['token'] + \
              "/sendMessage?chat_id={0}&text=".format(chat_id)
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

    def SendMessage(self, message, iduser=None):
        '''
        send message to chat
        '''
        message = message.replace("#", "_SHARP")
        message = message.replace("&", "_AMP")
        url = self._getUrl("send message", iduser)
        resp = self._sendCommand("GET", url+message)
        if resp.status_code == 200:
            print("OK, message is send")
        else:
            print("Message is not send!")
            print(resp.status_code, resp.text)
    def parseSenderMessage(self, message, iduser):
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
        data = {}

        #when action is not edn aand expectict further data from user
        if self.ACTION_EDIT_TASK_ID:
            if len(mes) < 2:
                return self.TYPE_ERROR, {"infos": "Command is too short!"}
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
        elif self.ACTION_EDIT_BOOKMARK_ID:
            bookmark_id = self.ACTION_EDIT_BOOKMARK_ID
            self.ACTION_EDIT_BOOKMARK_ID = None
            if len(mes) < 2:
                return self.TYPE_ERROR, {"infos": "Your messge is too short. Try again."}
            if mes[0] == "description":
                new_desc = re.search("[\"|'](.+)[\"|']", message).group(1)
                self.db.execute_script(self.bookmark.updateBookmarkQuery(bookmark_id, self._b64decenc(new_desc), "description"))
                return self.TYPE_BOOKMARKS, {"infos": "Bookmark is updated!"}
            return self.TYPE_ERROR, {"infos": "Wrong syntax!"}

        #main loop, check entered commands
        #there is next command: add, show, delete, set, exit,
        # bot(block of command for manage bot), edit, help(in plans:) )
        if mes[0] == "add":
            if len(mes) < 2:
                return self.TYPE_ERROR, {"infos": "Command is too short!"}
            if mes[1] == "task":
                new_task = re.search("[\"'](.+)[\"']", message).group(1)
                expire_date = re.search("\d{2}.\d{2}.\d{2,4}", message).group(0)
                if expire_date[-3:] != '.':
                    expire_date = expire_date[:-2] + "20" + expire_date[-2:]
                expire_date = expire_date[-4:] + "-" + expire_date[3:5] + "-" + expire_date[:2]
                return self.TYPE_NEW_TASK, {"task": new_task, "expire_date": expire_date}
            if mes[1] == "bookmark":
                if "https://" in  mes[2] or "https://" in mes[2]:
                    b64bookmark = self._b64decenc(mes[2])
                    self.db.execute_script(self.bookmark.createBookmarkQuery(b64bookmark, iduser=iduser))
                    return self.TYPE_BOOKMARKS, {"infos": "Bookmark is added!"}
                return self.TYPE_BOOKMARKS, {"infos": "Wrong syntax! Can't add bookmark!"}
            if mes[1] == "reminder":
                #add new reminder
                # syntax : add reminder "name" HH:MM [everyday,n times]
                found_text = re.search("[\"'](.+)[\"']", message)
                found_time = re.search("\d{2}:\d{2}", message)
                found_count = re.search("[0-9]+\stimes?$|everyday$", message)
                if not found_text or not found_count or not found_time:
                    return self.TYPE_ERROR, {"infos": "Wrong command syntax!"}
                name = found_text.group(1)
                time_to_remind = found_time.group(0)
                temp_count = found_count.group(0)
                if temp_count == "everyday":
                    count = -1
                else:
                    count = int(temp_count.split(' ')[0])
                if len(name) < 1 or len(time_to_remind) < 5:
                    return self.TYPE_REMINDERS, {"infos": "wrong syntax"}
                b64name = self._b64decenc(name)
                self.db.execute_script(self.reminder.createReminderQuery(b64name, time_to_remind, count, iduser))
                return self.TYPE_REMINDERS, {"infos": "Reminder is added!"}
        # show tasks either all or determined amount
        elif mes[0] == "show":
            if len(mes) < 2:
                return self.TYPE_ERROR, {"infos": "Command is too short!"}
            if mes[1] == "tasks":
                if len(mes) == 3 and mes[2].isdigit():
                    res = self.db.execute_script(self.task.getTasksQuery(mes[2]))
                else:
                    res = self.db.execute_script(self.task.getTasksQuery())
                return self.TYPE_SHOW_TASKS, {'tasks': res}
            if mes[1] == "bookmarks":
                if len(mes) == 3 and mes[2].isdigit():
                    db_res = self.db.execute_script(self.bookmark.getBookmarks(count=mes[2], iduser=iduser))
                else:
                    db_res = self.db.execute_script(self.bookmark.getBookmarks(iduser=iduser))
                if len(db_res) == 0:
                    return self.TYPE_BOOKMARKS, {'infos': "There are no bookmarks!"}
                send_mes = ""
                for bookmark in db_res:
                    if bookmark[1]:
                        send_mes += "Description: {0}, ".format(self._b64decenc(bookmark[1], encode=False))
                    if bookmark[2]:
                        send_mes += " rate: {0}, ".format(bookmark[2])
                    if mes[-1] == "full":
                        if bookmark[4]:
                            comments_ = self._b64decenc(bookmark[4], encode=False)
                            send_mes += " id: {0},\nComments: {1}\n".format(bookmark[3], comments_)
                        else:
                            send_mes += " id: {0}, ".format(bookmark[3])
                    send_mes += "URL: {0}\n".format(self._b64decenc(bookmark[0], encode=False))
                return self.TYPE_BOOKMARKS, {'infos': send_mes}
            if mes[1] == "reminders":
                reminders = self.db.execute_script(self.reminder.getRemindersQuery(iduser))
                
                message_to_send = ''
                if len(reminders) < 1:
                    message_to_send = "No reminders found!"
                else:
                    for r in reminders:
                        message_to_send += "Reminder name: {0}, alert time: {1}".format(self._b64decenc(r[1], encode=False), r[2])
                        if r[3] == -1:
                            message_to_send += " frequency: everyday"
                        else:
                            message_to_send += " freqency: {0}".format(r[3])
                    
                        if len(mes) > 2 and mes[2] == 'full':
                            message_to_send += ', id: {0}'.format(r[0])
                        message_to_send += "\n"
                return self.TYPE_REMINDERS, {"infos": message_to_send}
        #delete task
        elif mes[0] == "delete":
            if len(mes) < 4:
                return self.TYPE_ERROR, {"infos": "Command is too short!"}
            if mes[1] == "task" and mes[2] == "with" and mes[3] == "id":
                task_id = mes[4]
                
                [check_query, update_query] = self.task.removeTaskQuery(task_id)
                if not self.db.execute_script(check_query):
                    data['infos'] = "Wrong id! No task is deleted )"
                else:
                    self.db.execute_script(update_query)
                    data['infos'] = "Deleted task with id {0}".format(task_id)
                return self.TYPE_DELETE_TASK, data
            if mes[1] == "bookmark" and mes[2] == "with" and mes[3] == "id":
                if not mes[4].isdigit():
                    data['infos'] = "Wrong input"
                elif len(self.db.execute_script(self.bookmark.checkIdQuery(mes[4], iduser))) > 0:
                    self.db.execute_script(self.bookmark.deleteBookmarkQuery(mes[4], iduser))
                    data['infos'] = "Deleted bookmark with id: {0}".format(mes[4])
                else:
                    data['infos'] = "There are no such bookmark with id: {0}".format(mes[4])
                return self.TYPE_BOOKMARKS, data
            if mes[1] == "reminder" and mes[2] == "with" and mes[3] == "id":
                if not mes[4].isdigit():
                    return self.TYPE_ERROR, {"infos": "Wrong id format!"}
                [check_query, delete_query] = self.reminder.deleteReminderQuery(mes[4], iduser)
                if self.db.execute_script(check_query):
                    self.db.execute_script(delete_query)
                    message_to_send = "Reminder succesfully deleted!"
                else:
                    message_to_send = "No reminder found!"
                return self.TYPE_REMINDERS, {"infos": message_to_send}
        elif mes[0] == "update":
            if len(mes) < 4:
                return self.TYPE_ERROR, {"infos": "Command is too short!"}
            if mes[1] == "task" and mes[2] == "with" and mes[3] == "id":
                if mes[4] == "set" and mes[5] == 'done':
                    data = {}
                    if not self.db.execute_script(self.task.setTaskDoneQuery(mes[2])):
                        data['infos'] = "Task with id {0} is completed!".format(mes[2])
                    else:
                        data['infos'] = "Can't find task with id {0}".format(mes[2])
                    return self.TYPE_SET_TASK_DONE, data
                if mes[4].isdigit():
                    if self.db.execute_script(self.task.checkTaskIdQuery(mes[4])):
                        self.ACTION_EDIT_TASK_ID = mes[4]
                        return self.TYPE_EDIT_TASK, None
                    else:
                        self.SendMessage("No such task found!")
            elif mes[1] == "bookmark" and mes[2] == "with" and mes[3] == "id":
                if mes[4].isdigit():
                    ids = self.db.execute_script(self.bookmark.checkIdQuery(int(mes[4]), iduser))
                    if len(ids) >= 1:
                        self.ACTION_EDIT_BOOKMARK_ID = mes[4]
                        return self.TYPE_BOOKMARKS, {"infos": "Now edit choosen bookmark, example: description \"new description\" "}
                else:
                    return self.TYPE_ERROR, {"infos": "Need correct bookmark id!"}
            return self.TYPE_ERROR, {"infos": "Wrong syntax!"}
                        
                        
                    
        elif mes[0] == "habr":
            if len(mes) < 2:
                return self.TYPE_ERROR, {"infos": "Command is too short!"}
            if mes[1] == "show":
                return self.TYPE_HABR, {'infos': self.getHabrNewses()}
            elif mes[1] == "link":
                if len(mes) < 3:
                    return self.TYPE_ERROR, {"infos": "Command is too short!"}
                if self.habr_newses and int(mes[2]) in [news['index'] for news in self.habr_newses]:
                    record = [news for news in self.habr_newses if news['index'] == int(mes[2])][0]
                    data = {"infos": "Description: {0}\nhabr Link: {1}".format(record["desc"], record["link"])} 
                else:
                    data = {"infos": "No news found!"}
                return self.TYPE_HABR, data
            elif mes[1] == "remember":
                # add habr link to bookmarks
                if not self.habr_newses:
                    self.getHabrNewses()
                record = [news for news in self.habr_newses if news['index'] == int(mes[2])][0]
                b64link = self._b64decenc(record["link"])
                b64description = self._b64decenc(record["title"])
                b64comments = self._b64decenc(record["desc"])
                self.db.execute_script(self.bookmark.createBookmarkQuery(b64link, description=b64description, comments=b64comments, iduser=iduser))
                return self.TYPE_BOOKMARKS, {"infos": "Bookmark is added!"}
        elif mes[0] == "bot":
            if len(mes) < 2:
                return self.TYPE_ERROR, {"infos": "Command is too short!"}
            if mes[1] == "hello":
                return self.TYPE_SAY_HELLO, {"infos": "hello I'm bot :)"}
            elif mes[1] == "exit":
                return self.TYPE_EXIT, None
        return None, None
    def getHabrNewses(self):
        '''
        init self.habr_newses and send respod for 'habr show' command
        '''
        site = requests.get(HABRAHABR_MAIN)

        self.habr_newses = []
        soup = BS(site.text, 'lxml')
        links = soup.find_all("a", {"class", "post__title_link"})
        divs = soup.find_all("div", {"class", "html_format"})
        tags = re.compile("<.*?>")
        # blanks = re.compile("^\n$")
        indx = 1
        if len(links) != len(divs):
            return self.TYPE_ERROR, None
        for index, link in enumerate(links):
            news_links = re.findall("<a.+?href=\"(https://habrahabr.ru/[a-zA-Z/]+/[0-9]+?/)\">(.*?)</a>", str(link))
            desc = tags.sub('', str(divs[index]))
            # desc = blanks.sub('', desc)
            for link, title in news_links:
                self.habr_newses.append({"index": indx, "link": link, "title": title, "desc": desc})
            indx += 1
        infos = ""
        for news in self.habr_newses:
            infos += str(news["index"]) + ". " + news['title'] + "\n"
        return infos
    def CheckReminders(self):
        if self.one_minute_remind == time.strftime("%H:%M"):
            return
        self.one_minute_remind = time.strftime("%H:%M")
        reminders = self.db.execute_script(self.reminder.getRemindersQuery())
        current_time = time.strftime("%H:%M")
        for r in reminders:
            if current_time == r[2]:
                # iduser = int(r[4])
                chat_id = self.getSenderIdByTelegramId(r[4])
                self.SendMessage("Remind: '{0}'\n Get up and do your work!".format(self._b64decenc(r[1], encode=False)), chat_id)
                cnt = int(r[3])
                if cnt != -1:
                    cnt -=  1
                    if cnt > 0:
                        print(self.reminder.updateReminderQuery('counter', r[0], cnt, r[4]))
                        self.db.execute_script(self.reminder.updateReminderQuery('counter', r[0], cnt, r[4]))
                    else:
                        _, delete_query = self.reminder.deleteReminderQuery(str(r[0]), r[4])
                        self.db.execute_script(delete_query)
    def GetUpdates(self):
        '''
        get new updates, update updete_id in config, insert messages into db
        '''
        #get messages from Telegram API
        running_bot = True
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

        #process incoming message
        valid_user_id = int(self.getValidUserId())
        #there ara two types of message: "message" and "edited_message"
        type_of_message = ""
        for res in js_data['result']:
            for key in res.keys():
                if key != "update_id":
                    type_of_message = key
            sender_id = int(self.getSenderIdByTelegramId(res[type_of_message]["from"]["id"]))
            if valid_user_id != res[type_of_message]["from"]["id"]:
                continue
            action_type, data = self.parseSenderMessage(res[type_of_message]['text'].lower(), sender_id)
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
            elif action_type == self.TYPE_EXIT:
                # exit from bot
                self.SendMessage("Bot is down!")
                running_bot = False
            elif action_type == self.TYPE_EDIT_TASK:
                self.SendMessage("Enter new text or expire date(exaple text 'new text'):")
            elif action_type == self.TYPE_TASK_CHANGED:
                self.SendMessage("Successfully change task! Enter 'show tasks' to see other tasks :)")
            elif action_type == self.TYPE_BOOKMARKS or action_type == self.TYPE_HABR \
              or action_type == self.TYPE_REMINDERS or action_type == self.TYPE_SET_TASK_DONE \
              or action_type == self.TYPE_DELETE_TASK or action_type == self.TYPE_SAY_HELLO or action_type == self.TYPE_ERROR :
                self.SendMessage(data['infos'])
        # writing new config into file with incremented and updated update_id
        if self.config['last_updates'] <= max([mes["update_id"] for mes in js_data["result"]]):
            with open(CONFIG_NAME, 'w') as fd:
                self.config['last_updates'] = \
                 max([mes["update_id"] for mes in js_data["result"]])+1
                fd.write(str(self.config).replace("'", "\"").replace("False","false").replace("True","true"))
        return running_bot
    def Remind(self):
        '''
        reminder currently in develepment need to add some basic functionality
        '''
        current_data = time.strftime("%Y-%m-%d")
        current_time = time.strftime("%H%M")
        if current_time == "1900":
            to_date = "2017-" + self.calendar.getData(7)
            print("To date: ", to_date)
            messege_to_chat = "You have next tasks ahead:\n"
            for task in self.db.execute_script(self.task.getTaskForPeriodQuery(current_data, to_date)):
                messege_to_chat += task[1] + ", id: " + str(task[0]) + \
                  ", expires " + task[2] + "\n"
            self.SendMessage(messege_to_chat, ) 

    # tech function
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