import sys
import os
import threading
import time
import signal

from models.rabbitmq import RabbitMQ
from utils.logger import setup_logger
from handlers.zalo_handler import init_zalobot, run_zalo_listener
from handlers.message_handler import on_message_received

# Setup main logger
logger = setup_logger("Main")
exit_flag = threading.Event()

def run_zalobot():
    bot = init_zalobot()
    if bot is None:
        logger.error("Failed to init ZaloBot.")
        return
    run_zalo_listener(bot)

def main():
    zalo_thread = None
    try:
        signal.signal(signal.SIGINT, lambda sig, frame: exit_flag.set())

        # Create RabbitMQ
        logger.info("Creating RabbitMQ connection...")
        rabbitmq = RabbitMQ()
        if not rabbitmq.connect():
            sys.exit(1)

        logger.info("Creating consumer...")
        # prefetch
        rabbitmq.channel.basic_qos(prefetch_count=1)
        consumer_created = rabbitmq.consume(queue_name="XXX_QUEUE", callback=on_message_received)
        if not consumer_created:
            sys.exit(1)

        # Run ZaloBot in a separate thread
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