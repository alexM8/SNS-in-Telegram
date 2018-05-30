#!/usr/bin/env python3
import re, sys, json, config, telegram_api
import flask, flask.cli

app = flask.Flask(__name__)
tg = telegram_api.TelegramAPI(key=config.bot_key)
uid = tg.get_uid(config.username)

@app.route(config.http_location, methods=['POST'])
def receive():
    try:
        alert = flask.request.get_json()
        send(uid, prettify(alert))
    except Exception as e:
        send(uid, "Warning: Received an incoming data but failed to parse it\n%s" % e)
        telegram_api.print_message(e)
    return flask.Response(status=200)

def prettify(data):
    try:
        message = {}
        alert = ""
        data["Message"] = json.loads(data["Message"])
        for x in ["AlarmDescription", "NewStateReason"]:
            message[x] = data["Message"][x]
        for x in ["Namespace", "MetricName", "Period", "Threshold"]:
            message[x] = str(data["Message"]["Trigger"][x])
        for x in range(0, len(data["Message"]["Trigger"]["Dimensions"])):
            message["name"] = data["Message"]["Trigger"]["Dimensions"][x]["value"]
        subject = re.sub('ALARM:', config.emoji_map["DISASTER"] + " - ", data["Subject"]) + "\n"
        subject = re.sub('OK:', config.emoji_map["OK"] + " - ", subject)
        subject = re.sub('INSUFFICIENT:', config.emoji_map["WARNING"] + " - ", subject)
        alert += subject
        for key, value in message.items():
            alert += key + " - " + value + "\n"
    except Exception as e:
        alert = "Warning: Parsed incoming data, but failed to prettify it\n%s" % e
        telegram_api.print_message(e)
    return alert

def send(uid, data):
    try:
        tg.send_message(uid, data)
    except Exception as e:
        telegram_api.print_message(e)
    return "Success"

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
    sys.exit(flask.cli.main())
