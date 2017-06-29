#!/usr/bin/python3
'''
main module, handling commnd line arguments and implements main bussiness logic
'''
import subprocess as sb, time

def main():
    '''
    main function
    '''
    bt = sb.Popen("python3 server.py &", shell=True, stdout=sb.PIPE)
    while True:
        output_ = bt.stdout.read().decode('utf-8')
        if "Exit" in output_:
            print("Exiting...")
            break
        elif "Update" in output_:
            print("Updating bot...")
            sb.call("sleep 3; ./bot_script.sh update", shell=True)
            bt = sb.Popen("python3 server.py --restarted &", shell=True, stdout=sb.PIPE)
        elif "Restart" in output_:
            print("Restarting bot..")
            # sb.call("sleep 3; ./bot_script.sh restart", shell=True)
            time.sleep(2)
            bt = sb.Popen("python3 server.py --restarted &", shell=True, stdout=sb.PIPE)
        time.sleep(2)



if __name__ == "__main__":
    main()
