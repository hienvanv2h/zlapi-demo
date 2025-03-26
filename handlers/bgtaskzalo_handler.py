import time
import random
import json
from pydantic import BaseModel
from typing import Dict, Any
from uuid import UUID

from interfaces import IZaloBot
from utils.config import get_base_url
from utils.logger import get_logger

class BgTaskSendZalo(BaseModel):
    task_id: UUID
    phone_number: str
    message: str
    zip_file_url: str
    params: Dict[str, Any]

def on_notify_download_image(ch, method, properties, body, logger=None, bot: IZaloBot = None):
    logger = logger or get_logger("MessageHandler")
    text = body.decode('utf-8')

    try:
        # Payload format: <part1>|<part2>|<taskId>#<payload>
        taskId , payload_str = text.split("|")[-1].split("#")
        logger.info(f"Received message - Task ID: {taskId} - Payload: {payload_str}")

        payload_data = json.loads(payload_str)
        params = payload_data.get("Params") or {}
        payload = BgTaskSendZalo(
            task_id=payload_data["TaskId"],
            phone_number=payload_data["PhoneNumber"],
            message=payload_data["Message"],
            zip_file_url=payload_data["ZipFileUrl"],
            params=params
        )

        notify_message = f"{payload.message} {get_base_url()}{payload.zip_file_url.replace('\\', '/')}"

        if bot is None:
            logger.error("ZaloBot is None. Stop processing.")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return
        
        bot.notify_download_image(phone_number=payload.phone_number, message=notify_message)
    except ValueError as e:
        logger.error(f"Invalid message format: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        return
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        return
    
    ch.basic_ack(delivery_tag=method.delivery_tag)
    logger.info("Sent notification successfully.")