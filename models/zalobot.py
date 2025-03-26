from zlapi import ZaloAPI
from zlapi.models import *
from zlapi._message import Message
from interfaces import IZaloBot
from utils.logger import setup_logger

class ZaloBot(ZaloAPI, IZaloBot):
    def __init__(self, phone=None, password=None, imei=None, cookies=None, user_agent=None, auto_login=True, logger=None):
        super().__init__(phone, password, imei, cookies, user_agent, auto_login)
        self.logger = logger or setup_logger(name="ZaloBot", log_file="zalobot.log")

    def onMessage(self, mid=None, author_id=None, message=None, message_object=None, thread_id=None, thread_type=ThreadType.USER):
        if not isinstance(message, str):
            return
        
        if thread_type == ThreadType.USER:
            self.logger.info(f"Received message from USER - Thread ID: {thread_id}")
        elif thread_type == ThreadType.GROUP:
            self.logger.info(f"Received message from GROUP - Thread ID: {thread_id}")
        else:
            self.logger.info(f"Received message from UNKNOWN Thread type - Thread ID: {thread_id}")
        
        self.print_account_info(thread_id)

        user = self.fetchUserInfo(author_id)
        is_fr = user['changed_profiles'][f'{author_id}']['isFr']
        if is_fr is None:
            # Truy vấn danh sách bạn bè
            friends = self.fetchAllFriends()
            # Duyệt và kiểm tra nếu người dùng hiện tại đã là bạn
            for friend in friends:
                if friend.user_id == author_id:
                    is_fr = True
                    break

        # Gửi yêu cầu kết bạn
        if not is_fr:
            self.sendFriendRequest(
                author_id, (
                    "Chào bạn, đây là PLC Help Desk! "
                    "Hãy kết bạn với chũng tôi để nhận hỗ trợ."
                )
            )

    def print_account_info(self, userId):
        """
        In thông tin tài khoản người dùng
        """
        user = self.fetchUserInfo(userId)
        if not user or not isinstance(user, User):
            return
        self.logger.info(user)

    def print_group_info(self, groupId):
        """
        In thông tin nhóm
        """
        group = self.fetchGroupInfo(groupId)
        if not group or not isinstance(group, Group):
            return
        self.logger.info(group)

    def start_listener(self):
        try:
            self.logger.info("Starting listener...")
            self.listen()
            return True
        except Exception as e:
            self.logger.error(e)
            return False
        
    def notify_download_image(self, phone_number, message):
        """
        Gửi thông báo đến người dùng
        """
        profile = self.fetchPhoneNumber(phone_number)
        # self.logger.info(profile)

        user_id = profile["uid"]

        # Gửi thông báo
        self.sendMessage(
            thread_id=user_id,
            thread_type=ThreadType.USER,
            message=Message(text=message)
        )

        self.logger.info(f"Sent notification to {phone_number} successfully.")
