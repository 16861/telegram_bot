import bot as telegrambot

def main():
    bot = telegrambot.TelegramBot()
    while True:
        if not bot.GetUpdates():
            break
        bot.Remind()
    #print(bot.ShowNewMessages)
        

if __name__ == "__main__":
    main()