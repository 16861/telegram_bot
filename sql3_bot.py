import db_scripts,  sqlite3, os

class BotDB():
    def __init__(self):
        self.DBNAME = "botdb.sqlite3"
        #init scripts executed in case when there is no database
        self.initDB()
    def initDB(self):
        if os.path.exists(self.DBNAME):
            return 
        with sqlite3.connect(self.DBNAME) as conn:
            for script in db_scripts.ALL_SCRIPTS:
                conn.execute(script)
                conn.commit()
        # return True

    def execute_script(self, script):
        return_values = []
        with sqlite3.connect(self.DBNAME) as conn:
            return_values = conn.execute(script).fetchall()
        return return_values
        