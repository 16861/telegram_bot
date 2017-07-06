import requests, json, time, subprocess as sb



BASE_URL = "http://api.telegram.org/bot"
CONFIG_NAME = "masterbot.conf"

class MasterTelegramBot():
    def __init__(self):
        with open(CONFIG_NAME, 'r') as fd:
            self.config = json.loads(fd.read())
        self.slavebot = sb.Popen("python3 server.py --restart &", shell=True, stdout=sb.PIPE)

        self.SendMessage("Hello )")
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
    def GetUpdates(self):
        '''
        process updates that comes from user
        '''
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
        user_id = self.config['user_id']
        for res in js_data['result']:
            for key in res.keys():
                if key != "update_id":
                    type_of_message = key
            if user_id != res[type_of_message]["from"]["id"]:
                continue

            mes = res[type_of_message]['text'].lower().split(' ')
            if len(mes) == 0:
                continue
            if mes[0] == "slavebot":
                if len(mes) < 2:
                    response = "Wrong command!"
                else:
                    if mes[1] == "restart":
                        response = "Restarting bot..."
                        time.sleep(2)
                        pr = sb.run("ps aux | pgrep -f 'python3 server' | xargs kill -SIGTERM ", shell=True, stdout=sb.PIPE)
                        self.slavebot = sb.Popen("python3 server.py --restart &", shell=True, stdout=sb.PIPE)
                    elif mes[1] == "stop":
                        response = "Slave bot is down..."
                        time.sleep(2)
                        sb.run("ps aux | pgrep -f 'python3 server' | xargs kill -SIGTERM ", shell=True, stdout=sb.PIPE)
                    elif mes[1] == "start":
                        sb_process_number = sb.run("ps aux | pgrep -f 'python3 server'", shell=True, stdout=sb.PIPE)
                        processes_ = sb_process_number.stdout.decode('utf-8').split("\n")
                        if len(processes_) > 2:
                            response = "Slave bot is already running"
                        else:
                            self.slavebot = sb.Popen("python3 server.py --restart &", shell=True, stdout=sb.PIPE)
                            response = "Slave bot is running..."
                    elif mes[1] == "update":
                        sb.run("ps aux | pgrep -f 'python3 server' | xargs kill -SIGTERM", shell=True)
                        sb.run("./bot_script.sh update", shell=True)
                        self.slavebot = sb.Popen("python3 server.py --restart &", shell=True, stdout=sb.PIPE)
                        response = "Slave bot is updated!"
                    elif mes[1] == "status":
                        sb_process_number = sb.run("ps aux | pgrep -f 'python3 server'", shell=True, stdout=sb.PIPE)
                        processes_ = sb_process_number.stdout.decode('utf-8').split("\n")
                        if len(processes_) > 2:
                            response = "Slave bot is running"
                        else:
                            response = "Slave bot is down"
            elif mes[0] == "exit":
                running_bot = False
                response = "Bye )"
            elif mes[0] == "hello":
                response = "Hello, I'm master bot!"
            else:
                response = None
            if response:
                self.SendMessage(response)
            # writing new config into file with incremented and updated update_id
        with open(CONFIG_NAME, 'w') as fd:
            if self.config['last_updates'] <= max([mes["update_id"] for mes in js_data["result"]]):
                self.config['last_updates'] = \
                 max([mes["update_id"] for mes in js_data["result"]])+1
            self.config['last_updates'] = \
              max([mes["update_id"] for mes in js_data["result"]])+1
            fd.write(str(self.config).replace("'", "\"").replace("False","false").replace("True","true"))
        return running_bot