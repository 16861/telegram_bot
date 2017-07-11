# Telegram bot: reminder class
class Reminder():
    def __init__(self):
        pass
    #CRUD
    #create reminder record
    def createReminderQuery(self, text_, time_, count, userid = None):
        '''
        return creating reminder query
        '''
        if not userid:
            query = "INSERT INTO reminders(name, time_, count_) VALUES('{0}', '{1}', {2})".format(text_, time_, count)
        else:
            query = "INSERT INTO reminders(name, time_, count_, userid) VALUES('{0}', '{1}', {2}, {3})".format(text_, time_, count, userid)
        return query
    #delete reminder
    def deleteReminderQuery(self, id):
        '''
        return delete query
        if id is not of int type - return None
        '''
        if not id.isdigit():
            return None
        check_query = "SELECT id FROM reminders WHERE id = {0}".format(id)
        delete_query = "DELETE FROM reminders WHERE id = {0}".format(id)
        return [check_query, delete_query]
    #get reminders
    def getRemindersQuery(self, userid=None):
        '''
        '''
        if not userid:
            query = "SELECT * FROM reminders"
        else:
            query = "SELECT * FROM reminders WHERE userid={0}".format(id)
        return query
    #update reminder
    def updateReminderQuery(self, type, id, count_):
        '''
        '''
        if type == "counter":
            query = "UPDATE reminders SET count_ = {0} WHERE id = {1}".format(count_, id)
        else:
            query = None
        return query
