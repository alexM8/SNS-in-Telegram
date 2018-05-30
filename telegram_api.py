import requests, sys, random, os, sys, json, string, config


class TelegramAPI:
    tg_url_bot_general = "https://api.telegram.org/bot"

    def http_get(self, url):
        answer = requests.get(url, proxies=self.proxies)
        self.result = answer.json()
        self.ok_update()
        return self.result

    def __init__(self, key):
        self.debug = True
        self.key = config.bot_key
        self.proxies = {}
        self.type = "private"  # 'private' for private chats or 'group' for group chats
        self.markdown = False
        self.html = False
        self.disable_web_page_preview = False
        self.disable_notification = False
        self.reply_to_message_id = 0
        self.tmp_dir = None
        self.tmp_uids = None
        self.location = {"latitude": None, "longitude": None}
        self.update_offset = 0
        self.image_buttons = False
        self.result = None
        self.ok = None
        self.error = None

    def get_me(self):
        url = self.tg_url_bot_general + self.key + "/getMe"
        me = self.http_get(url)
        return me

    def get_updates(self):
        url = self.tg_url_bot_general + self.key + "/getUpdates"
        params = {"offset": self.update_offset}
        if self.debug:
            print_message(url)
        answer = requests.post(url, params=params, proxies=self.proxies)
        self.result = answer.json()
        if self.debug:
            print_message("Content of /getUpdates:")
            print_message(self.result)
        self.ok_update()
        return self.result

    def send_message(self, to, message):
        url = self.tg_url_bot_general + self.key + "/sendMessage"
        params = {"chat_id": to, "text": message, "disable_web_page_preview": self.disable_web_page_preview,
                  "disable_notification": self.disable_notification}
        if self.reply_to_message_id:
            params["reply_to_message_id"] = self.reply_to_message_id
        if self.markdown or self.html:
            parse_mode = "HTML"
            if self.markdown:
                parse_mode = "Markdown"
            params["parse_mode"] = parse_mode
        if self.debug:
            print_message("Trying to /sendMessage:")
            print_message(url)
            print_message("post params: " + str(params))
        answer = requests.post(url, params=params, proxies=self.proxies)
        if answer.status_code == 414:
            self.result = {"ok": False, "description": "414 URI Too Long"}
        else:
            self.result = answer.json()
        self.ok_update()
        return self.result

    def update_message(self, to, message_id, message):
        url = self.tg_url_bot_general + self.key + "/editMessageText"
        message = "\n".join(message)
        params = {"chat_id": to, "message_id": message_id, "text": message,
                  "disable_web_page_preview": self.disable_web_page_preview,
                  "disable_notification": self.disable_notification}
        if self.markdown or self.html:
            parse_mode = "HTML"
            if self.markdown:
                parse_mode = "Markdown"
            params["parse_mode"] = parse_mode
        if self.debug:
            print_message("Trying to /editMessageText:")
            print_message(url)
            print_message("post params: " + str(params))
        answer = requests.post(url, params=params, proxies=self.proxies)
        self.result = answer.json()
        self.ok_update()
        return self.result

    def send_photo(self, to, message, path):
        url = self.tg_url_bot_general + self.key + "/sendPhoto"
        message = "\n".join(message)
        if self.image_buttons:
            reply_markup = json.dumps({"inline_keyboard": [[
                {"text": "R", "callback_data": "graph_refresh"},
                {"text": "1h", "callback_data": "graph_period_3600"},
                {"text": "3h", "callback_data": "graph_period_10800"},
                {"text": "6h", "callback_data": "graph_period_21600"},
                {"text": "12h", "callback_data": "graph_period_43200"},
                {"text": "24h", "callback_data": "graph_period_86400"},
            ], ]})
        else:
            reply_markup = json.dumps({})
        params = {"chat_id": to, "caption": message, "disable_notification": self.disable_notification,
                  "reply_markup": reply_markup}
        if self.reply_to_message_id:
            params["reply_to_message_id"] = self.reply_to_message_id
        files = {"photo": open(path, 'rb')}
        if self.debug:
            print_message("Trying to /sendPhoto:")
            print_message(url)
            print_message(params)
            print_message("files: " + str(files))
        answer = requests.post(url, params=params, files=files, proxies=self.proxies)
        self.result = answer.json()
        self.ok_update()
        return self.result

    def send_txt(self, to, text, text_name=None):
        path = self.tmp_dir + "/" + "zbxtg_txt_"
        url = self.tg_url_bot_general + self.key + "/sendDocument"
        text = "\n".join(text)
        if not text_name:
            path += "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(10))
        else:
            path += text_name
        path += ".txt"
        file_write(path, text)
        params = {"chat_id": to, "caption": path.split("/")[-1], "disable_notification": self.disable_notification}
        if self.reply_to_message_id:
            params["reply_to_message_id"] = self.reply_to_message_id
        files = {"document": open(path, 'rb')}
        if self.debug:
            print_message("Trying to /sendDocument:")
            print_message(url)
            print_message(params)
            print_message("files: " + str(files))
        answer = requests.post(url, params=params, files=files, proxies=self.proxies)
        self.result = answer.json()
        self.ok_update()
        return self.result

    def get_uid(self, name):
        uid = 0
        if self.debug:
            print_message("Getting uid from /getUpdates...")
        updates = self.get_updates()
        for m in updates["result"]:
            if "message" in m:
                chat = m["message"]["chat"]
            elif "edited_message" in m:
                chat = m["edited_message"]["chat"]
            else:
                continue
            if chat["type"] == self.type == "private":
                if "username" in chat:
                    if chat["username"] == name:
                        uid = chat["id"]
            if (chat["type"] == "group" or chat["type"] == "supergroup") and self.type == "group":
                if "title" in chat:
                    if chat["title"] == name.decode("utf-8"):
                        uid = chat["id"]
        return uid

    def error_need_to_contact(self, to):
        if self.type == "private":
            print_message("User '{0}' needs to send some text bot in private".format(to))
        if self.type == "group":
            print_message("You need start a conversation with your bot first in '{0}' group chat, type '/start@{1}'"
                          .format(to, self.get_me()["result"]["username"]))

    def update_cache_uid(self, name, uid, message="Add new string to cache file"):
        cache_string = "{0};{1};{2}\n".format(name, self.type, str(uid).rstrip())
        # FIXME
        if self.debug:
            print_message("{0}: {1}".format(message, cache_string))
        with open(self.tmp_uids, "a") as cache_file_uids:
            cache_file_uids.write(cache_string)
        return True

    def get_uid_from_cache(self, name):
        if self.debug:
            print ("Trying to read cached uid for {0}, {1}, from {2}".format(name, self.type, self.tmp_uids))
        uid = 0
        if os.path.isfile(self.tmp_uids):
            with open(self.tmp_uids, 'r') as cache_file_uids:
                cache_uids_old = cache_file_uids.readlines()
            for u in cache_uids_old:
                u_splitted = u.split(";")
                if name == u_splitted[0] and self.type == u_splitted[1]:
                    uid = u_splitted[2]
        return uid

    def send_location(self, to, coordinates):
        url = self.tg_url_bot_general + self.key + "/sendLocation"
        params = {"chat_id": to, "disable_notification": self.disable_notification,
                  "latitude": coordinates["latitude"], "longitude": coordinates["longitude"]}
        if self.reply_to_message_id:
            params["reply_to_message_id"] = self.reply_to_message_id
        if self.debug:
            print_message("Trying to /sendLocation:")
            print_message(url)
            print_message("post params: " + str(params))
        answer = requests.post(url, params=params, proxies=self.proxies)
        self.result = answer.json()
        self.ok_update()
        return self.result

    def answer_callback_query(self, callback_query_id, text=None):
        url = self.tg_url_bot_general + self.key + "/answerCallbackQuery"
        if not text:
            params = {"callback_query_id": callback_query_id}
        else:
            params = {"callback_query_id": callback_query_id, "text": text}
        answer = requests.post(url, params=params, proxies=self.proxies)
        self.result = answer.json()
        self.ok_update()
        return self.result

    def ok_update(self):
        self.ok = self.result["ok"]
        if self.ok:
            self.error = None
        else:
            self.error = self.result["description"]
            print_message(self.error)
        return True

def print_message(message):
    message = str(message) + "\n"
    filename = sys.argv[0].split("/")[-1]
    sys.stderr.write(filename + ": " + message)

def file_write(filename, text):
    with open(filename, "w") as fd:
        fd.write(str(text))
    return True