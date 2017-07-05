import time

class Task():
    def __init__(self):
        pass
    #CRUD
    def insertNewTaskQuery(self, text, expire_date, update_id, sender_id, chat_id):
        query = "INSERT INTO messages"+ \
          "(text, expire_date, update_id, sender_id, chat_id, insert_date, done, deleted, type)" + \
          " VALUES('{0}', '{1}', '{2}', {3}, {4}, '{5}', {6}, {7}, {8})".format( \
          text, expire_date, update_id, sender_id, chat_id, time.strftime("%Y-%m-%d %H:%M:%S"), 0, 0, 1)
        return query
    def getTasksInfosQuery(self, limit=None):
        '''
        if limit == None return all tasks
        '''
        if not limit:
            query = "SELECT id, text, expire_date FROM messages WHERE deleted = 0 AND done  = 0 AND type = 1 ORDER BY expire_date"
        else:
            query = "SELECT id, text, expire_date FROM messages WHERE deleted = 0 AND done = 0 AND type = 1 ORDER BY expire_date LIMIT {0}".format(limit)
        return query
    def getTaskForPeriodQuery(self, start_date, end_date):
        query = "SELECT id, text, expire_date FROM messages WHERE expire_date \
          BETWEEN '{0}' AND '{1}' AND type = 1 ORDER BY expire_date".format(start_date, end_date)
        return query
    def removeTaskQuery(self, id):
        '''
        removing task from db. row is not completely deleted 
        but field deleted changed to 1
        '''
        update_query = "UPDATE messages SET deleted = 1 WHERE id = {0}".format(id)
        check_query = "SELECT id FROM messages WHERE id = {0}".format(id)
        return [check_query, update_query]
    def setTaskDoneQuery(self, id):
        '''
        mark task as complete
        '''
        update_query = "UPDATE messages SET done = 1 WHERE id = {0}".format(id)
        check_query = "SELECT id FROM messages WHERE id = {0}".format(id)
        return [check_query, update_query]
    def updeteTaskQuery(self, id, new_data, type):
        query = None
        if type == "text":
            query = "UPDATE messages SET text = '{1}' WHERE id = {0}".format(id, new_data)
        elif type == "date":
            query = "UPDATE messages SET expire_date = '{1}' WHERE id = {0}".format(id, new_data)
        return query
    # additional
    def checkTaskIdQuery(self, id):
        query = "SELECT id FROM messages WHERE id = {0}".format(id)
        return query
    def getTasksQuery(self, limit=None):
        '''
        if limit == None return all tasks
        '''
        if not limit:
            query = "SELECT id, text, expire_date FROM messages WHERE deleted = 0 AND done  = 0 AND type = 1 ORDER BY expire_date"
        else:
            query = "SELECT id, text, expire_date FROM messages WHERE deleted = 0 AND done = 0 AND type = 1 ORDER BY expire_date LIMIT {0}".format(limit)
        return query