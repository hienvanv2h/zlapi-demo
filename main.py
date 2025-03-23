import sys
import os
import json
import threading
import time
import signal
import random
from dotenv import load_dotenv

from models.rabbitmq import RabbitMQ
from models.zalobot import ZaloBot
from utils.logger import setup_logger

# Setup main logger
logger = setup_logger("Main")
exit_flag = threading.Event()

def on_message_received(ch, method, properties, body):
    processing_time = random.randint(1, 5)
    text = body.decode('utf-8')
    logger.info(f"Received: {text} - Processing time: {processing_time} seconds")
    time.sleep(processing_time)

    ch.basic_ack(delivery_tag=method.delivery_tag)
    logger.info("Finished processing message")


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
        logger.error("Cookies file not found.")
        sys.exit(1)
        return None
    except json.JSONDecodeError:
        logger.error("Failed to decode cookies. Check cookies.json file.")
        sys.exit(1)
        return None
    return phone, password, imei, cookies

def run_zalobot():
    zalo_info = load_zalo_info()
    if zalo_info is None:
        logger.error("Failed to load Zalo credentials.")
        return
    phone, password, imei, cookies = zalo_info
    bot = ZaloBot(phone=phone, password=password, imei=imei, cookies=cookies)

    self_id = bot.user_id
    print("Current user:")
    bot.printAccountInfo(self_id)
    try:
        bot.listen()
    except Exception as e:
        logger.error(e)

def main():
    try:
        signal.signal(signal.SIGINT, lambda sig, frame: exit_flag.set())

        logger.info("Creating RabbitMQ connection...")
        rabbitmq = RabbitMQ()
        if not rabbitmq.connect():
            sys.exit(1)

        # Create comsumer
        logger.info("Creating consumer...")

        # prefetch
        rabbitmq.channel.basic_qos(prefetch_count=1)

        consumer_created = rabbitmq.consume("test-queue", on_message_received)
        if not consumer_created:
            sys.exit(1)

        # Run ZaloBot
        logger.info("Running ZaloBot...")
        zalo_thread = threading.Thread(target=run_zalobot, daemon=True)
        zalo_thread.start()
    
        # Keep main thread alive
        while not exit_flag.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt. Shutting down...")
        exit_flag.set()
    finally:
        # Cleanup
        logger.info("Closing RabbitMQ connection...")
        rabbitmq.close()
            
        if zalo_thread and zalo_thread.is_alive():
            zalo_thread.join(timeout=3)

            if zalo_thread.is_alive():
                logger.warning("ZaloBot thread is still alive. Forcing exit...")
                os._exit(0)

        logger.info("Application shutdown complete.")
        return

if __name__ == "__main__":
    main()