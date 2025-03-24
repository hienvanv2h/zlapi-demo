from models.zalobot import ZaloBot
from utils.config import load_zalo_credentials
from utils.logger import get_logger

__all__ = ["init_zalobot", "run_zalo_listener"]

logger = get_logger("ZaloHandler")

def init_zalobot():
    credentials = load_zalo_credentials()
    if credentials is None:
        logger.error("Failed to load Zalo credentials.")
        return None
    
    try:
        bot = ZaloBot(
            phone=credentials["phone"],
            password=credentials["password"],
            imei=credentials["imei"],
            cookies=credentials["cookies"]
        )

        self_id = bot.user_id
        print(f"ZaloBot created - User")
        bot.printAccountInfo(self_id)
        return bot
    except Exception as e:
        logger.error(e)
        return None

def run_zalo_listener(bot):
    if bot is None:
        logger.error("ZaloBot is not initialized.")
        return False
    try:
        logger.info("Starting listener...")
        bot.listen()
        return True
    except Exception as e:
        logger.error(e)
        return False