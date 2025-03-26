import os
import sys
import json
from dotenv import load_dotenv
from utils.logger import get_logger

logger = get_logger("Config")

# Tải thông tin tài khoản Zalo
def load_zalo_credentials():
    """Load Zalo credentials from .env and cookies file"""
    load_dotenv()
    phone = os.getenv("ZALO_PHONE")
    password = os.getenv("ZALO_PASSWORD")
    imei = os.getenv("ZALO_IMEI")
    cookies_filepath = os.getenv("ZALO_COOKIES_PATH")

    if not any([phone, password, imei, cookies_filepath]):
        logger.error("Missing Zalo credentials.")
        return None

    cookies = {}
    try:
        with open(cookies_filepath, "r") as f:
            cookies = json.load(f)
    except FileNotFoundError:
        logger.error("Cookies file not found.")
        sys.exit(1)
        return None
    except json.JSONDecodeError:
        logger.error("Failed to decode cookies. Check cookies.json file.")
        sys.exit(1)
        return None
    return {
        "phone": phone,
        "password": password,
        "imei": imei,
        "cookies": cookies
    }

def get_base_url():
    load_dotenv()
    return os.getenv("BASE_URL")

def get_prefix_id():
    load_dotenv()
    return os.getenv("PREFIX_ID")