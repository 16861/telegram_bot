#!/usr/bin/python3
'''
main module, handling commnd line arguments and implements main bussiness logic
'''
import bot as telegrambot

def main():
    '''
    main function
    '''
    bot = telegrambot.TelegramBot()
    while False:
        if not bot.GetUpdates():
            break
        bot.Remind()
        bot.SleepFor()

if __name__ == "__main__":
    main()
