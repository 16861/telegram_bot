# Telegram bot: reminder class
class Reminder():
    def __init__(self):
        pass
    #CRUD
    #create reminder record
    def createReminderQuery(self, text_, time_, count, iduser = None):
        '''
        return creating reminder query
        '''
        if not iduser:
            query = "INSERT INTO reminders(name, time_, count_) VALUES('{0}', '{1}', {2})".format(text_, time_, count)
        else:
            query = "INSERT INTO reminders(name, time_, count_, iduser) VALUES('{0}', '{1}', {2}, {3})".format(text_, time_, count, iduser)
        return query
    #delete reminder
    def deleteReminderQuery(self, id_, iduser):
        '''
        return delete query
        if id is not of int type - return None
        '''
        if not id_.isdigit():
            return None
        check_query = "SELECT id FROM reminders WHERE id = {0} AND iduser = {1}".format(id_, iduser)
        delete_query = "DELETE FROM reminders WHERE id = {0} AND iduser = {1}".format(id_, iduser)
        return [check_query, delete_query]
    #get reminders
    def getRemindersQuery(self, iduser=None):
        '''
        '''
        if not iduser:
            query = "SELECT * FROM reminders"
        else:
            query = "SELECT * FROM reminders WHERE iduser={0}".format(iduser)
        return query
    #update reminder
    def updateReminderQuery(self, type_, id_, count_, iduser):
        '''
        '''
        if type_ == "counter":
            query = "UPDATE reminders SET count_ = {0} WHERE id = {1} AND iduser ={2}".format(count_, id_, iduser)
        else:
            query = None
        return query
