import bot, argparse

parser = argparse.ArgumentParser()
parser.add_argument('--restarted', action="store_true")
args = parser.parse_args()
bot = bot.TelegramBot()
if args.restarted:
    bot.SendMessage("I am up! )")
while True:
    if not bot.GetUpdates():
        break
    # bot.Remind()
    bot.SleepFor(2)

if bot.RestartBotFlag:
    print("Restart bot")
elif bot.UpdateBotFlag:
    print("Update bot")
else:
    print("Exit")

