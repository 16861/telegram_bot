from flask import Flask, make_response
import json, os

app = Flask(__name__)

FLASK_CONFIG = "flask.conf"
BOT_CONFIG = "../bot.conf"
js_conf = {}

def read_conf():
    global js_conf
    content = ""
    with open(FLASK_CONFIG, 'r')  as fd:
        content = fd.read()
    js_conf = json.loads(content)

@app.route("/api/v0.1/update/<string:token>", methods=['GET'])
def updateBot(token):
    if token == js_conf["token"]:
        os.system("../bot_script.sh update")
        return make_response(json.dumps({"response": "OK, update proceed succesfull!"}) + "\n", 200)
    else:
        return make_response(json.dumps({"result": "Error!"}) + "\n", 404)

@app.route("/api/v0.1/stop/<string:token>", methods=['GET'])
def stopBot(token):
    if token == js_conf["token"]:
        content = ""
        with open(BOT_CONFIG, 'r')  as fd:
            content = fd.read()
        js_bot_conf = json.loads(content)
        js_bot_conf["stop_bot"] = True
        with open(BOT_CONFIG, 'w')  as fd:
            fd.write(str(js_bot_conf).replace("'", "\"").replace("True","true"))
        return make_response(json.dumps({"result": "Ok, but is stopping!"}) + "\n", 200)
    else:
        return make_response(json.dumps({"result": "Error!"}) + "\n", 404)

@app.route("/api/v0.1/start/<string:token>", methods=["GET"])
def startBot(token):
    if token == js_conf["token"]:
        os.system("../bot_script.sh start")
        return make_response(json.dumps({"result": "Ok, but is starting!"}) + "\n", 200)
    else:
        return make_response(json.dumps({"result": "Error!"}) + "\n", 404)

if __name__ == "__main__":
    read_conf()
    app.run(debug=True)