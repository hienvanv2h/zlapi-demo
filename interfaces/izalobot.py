from abc import ABC, abstractmethod

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
    def notify_download_image(self, phone_number, message):
        pass
