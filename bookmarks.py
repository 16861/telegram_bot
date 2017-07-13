class Bookmark():
    '''
    joined class for managing bookmarks and tags to them.
    implement CRUD in 
    '''
    def __init__(self):
        pass
    #CRUD for bookmarks
    #create bookmark
    def createBookmarkQuery(self, url_, iduser = None, description=None, comments=None, rate=None):
        if not description:
            description = ""
        if not rate:
            rate = 0
        if not iduser:
            iduser = 0
        if not comments:
            comments = ""
        query = "insert into bookmarks(url, description, rate, iduser, comments) values('{0}','{1}',{2}, {3}, '{4}')".format(url_, description, rate, iduser, comments)
        return query

    #read bookmark
    def getBookmarks(self, tags=None, count=None):
        if not count or type(count) != int :
            query = "SELECT url, description, rate, id, comments FROM bookmarks "
        else:
            query = "SELECT url, description, rate, i, comments FROM bookmarks LIMIT {0}".format(count)
        return query

    #update bookmark
    def updateBookmarkQuery(self, id, new_data, type='url'):
        if type == "url":
            query = "UPDATE bookmarks SET url = {0} WHERE id = {1}".format(new_data, id)
        elif type == "description":
            query = "UPDATE bookmarks SET description = {0} WHERE id = {1}".format(new_data, id)
        elif type == "rate":
            query = "UPDATE bookmarks SET rate = {0} WHERE id = {1}".format(new_data, id)
        else:
            return None
        return query

    #delete bookmark
    def deleteBookmarkQuery(self, id):
        query = "DELETE FROM bookmarks WHERE id = {0}".format(id)
        return query

    #others
    def checkIdQuery(self, id):
        query = "SELECT id FROM bookmarks WHERE id={0}".format(id)
        return query

    #Tags section
    #CRUD for tags