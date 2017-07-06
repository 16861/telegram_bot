import masterbot


def main():
    mbot = masterbot.MasterTelegramBot()
    while True:
        if not mbot.GetUpdates():
            break
if __name__ == "__main__":
    main()
    