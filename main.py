import sys
import os
import threading
import time
import signal

from models.rabbitmq import RabbitMQ
from utils.logger import setup_logger
from handlers.zalo_handler import init_zalobot
from handlers.bgtaskzalo_handler import on_notify_download_image
from utils.config import get_prefix_id

# Setup main logger
logger = setup_logger("Main")
exit_flag = threading.Event()

def main():
    zalo_thread = None
    try:
        signal.signal(signal.SIGINT, lambda sig, frame: exit_flag.set())

        # Run ZaloBot in a separate thread
        bot = init_zalobot()
        if bot is None:
            logger.error("Failed to init ZaloBot because it is None.")
            sys.exit(1)
        
        logger.info("Running ZaloBot...")
        zalo_thread = threading.Thread(target=bot.start_listener, daemon=True)
        zalo_thread.start()

        # Create RabbitMQ
        logger.info("Creating RabbitMQ connection...")
        rabbitmq = RabbitMQ(bot=bot)
        if not rabbitmq.connect():
            sys.exit(1)

        logger.info("Creating consumer...")
        # prefetch
        # rabbitmq.channel.basic_qos(prefetch_count=1)

        prefix_id = get_prefix_id()
        consumer_created = rabbitmq.consume(
            queue_name=f"{prefix_id}_NOTIFY_ZALO", 
            callback=on_notify_download_image
        )
        if not consumer_created:
            sys.exit(1)
    
        # Keep main thread alive
        while not exit_flag.is_set():
            time.sleep(0.1)
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