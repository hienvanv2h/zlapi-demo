from zlapi import ZaloAPI
from zlapi.models import *
from dotenv import load_dotenv
import os
import json
from zlapi.logging import Logging

logger = Logging(theme="catppuccin-mocha", text_color="white", log_text_color="black")

load_dotenv()
phone = os.getenv("ZALO_PHONE")
password = os.getenv("ZALO_PASSWORD")
imei = os.getenv("ZALO_IMEI")

cookies = {}
try:
    with open("cookies.json", "r") as f:
        cookies = json.load(f)
except FileNotFoundError:
    print("Cookies file not found. Logging in fresh...")
except json.JSONDecodeError:
    print("Failed to decode cookies. Check cookies.json file.")

# Test zalo id list to send message
id_list = [
    ###
]

class CustomBot(ZaloAPI):
    def __init__(self, phone=None, password=None, imei=None, cookies=None, user_agent=None, auto_login=True):
        super().__init__(phone, password, imei, cookies, user_agent, auto_login)
        count = 5
        for i in range(count):
            for receiver_id in id_list:
                self.sendMessage(Message(text=f"Hello {i+1}/{count}"), receiver_id, ThreadType.USER, mark_message="urgent")

    def onMessage(self, mid=None, author_id=None, message=None, message_object=None, thread_id=None, thread_type=ThreadType.USER):
        if not isinstance(message, str):
            return
        
        logger.info(f"Thread ID: {thread_id}")
        if thread_type == ThreadType.USER:
            self.printAccountInfo(author_id)
        elif thread_type == ThreadType.GROUP:
            self.printGroupInfo(author_id)
        else:
            return

    def printAccountInfo(self, userId):
        user = self.fetchUserInfo(userId)
        if not user or not isinstance(user, User):
            return
        logger.info(f"User info: {user}")

    def printGroupInfo(self, groupId):
        group = self.fetchGroupInfo(groupId)
        if not group or not isinstance(group, Group):
            return
        logger.info(f"Group info: {group}")


bot = CustomBot(phone=phone, password=password, imei=imei, cookies=cookies)
bot.listen()