class BotCalendar():
    def __init__(self, day=None, month=None, year=None):
        self._day = int(day)
        self._month = int(month)
        self._year = int(year)
        self._month_days = {"1" : 31, "2" : 28, "3" : 31, \
          "4" : 30, "5" : 31, "6" : 30, "7" : 31, "8" : 31, \
           "9" : 30, "10" : 31, "11" : 30, "12" : 31}
    def getData(self, after_days):
        '''
        return date DD.MM evaluate as current day in self._day + after_days
        correction on month also is made
        altough no yaer correction is made for now
        '''
        if after_days < 0 or after_days > 30:
            after_days = 7
        days_in_month = self._month_days[str(self._month)]
        return_str = ""
        
        if self._day+after_days > days_in_month:
            return_day = (self._day + after_days) - days_in_month
            return_month = self._month+1
        else:
            return_day = self._day + after_days
            return_month = self._month
        
        if return_month <= 9:
            return_str += "0"+str(return_month)
        else:
            return_str += str(return_month)
        return_str += "-"

        if return_day <= 9:
            return_str += "0"+str(return_day)
        else:
            return_str += str(return_day)       

        return return_str
    # getters and setters for month, year and day
    def set_day(self, day):
        self._day = day
    def get_day(self):
        return self._day
    def set_month(self, month):
        self._month = month
    def get_month(self):
        return self._month
    def set_year(self, year):
        self._year = year
    def get_year(self):
        return self._year