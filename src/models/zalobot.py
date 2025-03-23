from zlapi import ZaloAPI
from zlapi.models import *
from zlapi.logging import Logging

logger = Logging(theme="catppuccin-mocha", text_color="white", log_text_color="black")

class ZaloBot(ZaloAPI):
    def __init__(self, phone=None, password=None, imei=None, cookies=None, user_agent=None, auto_login=True):
        super().__init__(phone, password, imei, cookies, user_agent, auto_login)

    def onMessage(self, mid=None, author_id=None, message=None, message_object=None, thread_id=None, thread_type=ThreadType.USER):
        if not isinstance(message, str):
            return
        
        if thread_type == ThreadType.USER:
            logger.info(f"Received message from USER - Thread ID: {thread_id}")
        elif thread_type == ThreadType.GROUP:
            logger.info(f"Received message from GROUP - Thread ID: {thread_id}")
        else:
            logger.info(f"Received message from UNKNOWN Thread type - Thread ID: {thread_id}")
        
        self.printAccountInfo(author_id)

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

    def printAccountInfo(self, userId):
        """
        In thông tin tài khoản người dùng
        """
        user = self.fetchUserInfo(userId)
        if not user or not isinstance(user, User):
            return
        logger.info(f"User: {user}")

    def printGroupInfo(self, groupId):
        """
        In thông tin nhóm
        """
        group = self.fetchGroupInfo(groupId)
        if not group or not isinstance(group, Group):
            return
        logger.info(f"Group info: {group}")
