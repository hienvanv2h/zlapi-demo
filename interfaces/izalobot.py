from abc import ABC, abstractmethod
from zlapi._threads import ThreadType

class IZaloBot(ABC):
    @abstractmethod
    def print_account_info(self, userId):
        pass

    @abstractmethod
    def print_group_info(self, groupId):
        pass

    @abstractmethod
    def start_listener(self):
        pass

    @abstractmethod
    def send_message(self, phone_number, message, thread_type: ThreadType = ThreadType.USER):
        pass