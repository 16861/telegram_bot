import time, os

LOG_DIR="logs"

DEBUG_LEVEL = 10
WARN_LEVEL = 20
INFO_LEVEL = 30
ERROR_LEVEL = 40

class Logger():
    def __init__(self):
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)
        self._filename = LOG_DIR + "/bot_" + time.strftime("%Y-%m-%d")+ ".txt"
    def writeLog(self, level, message):
        with open(self._filename, 'a') as fd:
            if level == DEBUG_LEVEL:
                fd.write(time.strftime("%Y-%m-%d %H:%M:%S") + " DEBUG " + message + \
                 "\n")
            elif level == WARN_LEVEL:
                fd.write(time.strftime("%Y-%m-%d %H:%M:%S") + " WARNING " + \
                 message + "\n")
            elif level == INFO_LEVEL:
                fd.write(time.strftime("%Y-%m-%d %H:%M:%S") + " INFO " + message + \
                 "\n")
            elif level == ERROR_LEVEL:
                fd.write(time.strftime("%Y-%m-%d %H:%M:%S") + " ERROR " + message + \
                 "\n")