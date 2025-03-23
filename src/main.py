import sys
import os
import json
from dotenv import load_dotenv

from models.rabbitmq import RabbitMQ
from models.zalobot import ZaloBot

# Kết nối RabbitMQ
def create_rabbitmq_connection():
    try:
        rabbitmq = RabbitMQ()
    except Exception as e:
        print(f"[RabbitMQ] Critical Error: {e}")
        sys.exit(1)

    return rabbitmq

def on_message_received(ch, method, properties, body):
    text = body.decode('utf-8')
    print(f"[RabbitMQ] Received message from RabbitMQ: {text}")

# Tải thông tin tài khoản Zalo
def load_zalo_info():
    load_dotenv()
    phone = os.getenv("ZALO_PHONE")
    password = os.getenv("ZALO_PASSWORD")
    imei = os.getenv("ZALO_IMEI")
    cookies_filepath = os.getenv("ZALO_COOKIES_PATH")

    cookies = {}
    try:
        with open(cookies_filepath, "r") as f:
            cookies = json.load(f)
    except FileNotFoundError:
        print("Cookies file not found. Logging in fresh...")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Failed to decode cookies. Check cookies.json file.")
        sys.exit(1)
    return phone, password, imei, cookies

def main():
    print("[RabbitMQ] Creating RabbitMQ connection...")
    rabbitmq = create_rabbitmq_connection()
    try:
        rabbitmq.consume("test-queue", on_message_received)
    except Exception as e:
        print(f"[RabbitMQ] Failed to consume messages: {e}")
        sys.exit(1)
    finally:
        rabbitmq.close()

    phone, password, imei, cookies = load_zalo_info()
    bot = ZaloBot(phone=phone, password=password, imei=imei, cookies=cookies)

    self_id = bot.user_id
    print("Current user:")
    bot.printAccountInfo(self_id)
    bot.listen()


if __name__ == "__main__":
    main()