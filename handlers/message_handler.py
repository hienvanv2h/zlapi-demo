import time
import random
from utils.logger import get_logger

logger = get_logger("MessageHandler")

def on_message_received(ch, method, properties, body):
    processing_time = random.randint(1, 5)
    text = body.decode('utf-8')
    logger.info(f"Received: {text} - Processing time: {processing_time} seconds")
    time.sleep(processing_time)

    # text = body.decode('utf-8')
    # logger.info(f"Received message: {text}")

    ch.basic_ack(delivery_tag=method.delivery_tag)
    logger.info("Finished processing message")