import time
import random
import json
from pydantic import BaseModel
from typing import Dict, Any, Callable
from uuid import UUID

from interfaces import IZaloBot
from utils.config import get_base_url
from utils.logger import get_logger

class BgTaskNotifyZalo(BaseModel):
    task_id: UUID
    action_type: str
    phone_number: str
    message: str | None
    zip_file_url: str | None
    params: Dict[str, Any] | None

def on_notify_download_image(ch, method, properties, body, bot: IZaloBot = None, **kwargs):
    logger = kwargs.get("logger") or get_logger("MessageHandler")
    text = body.decode('utf-8')

    try:
        # Payload format: <part1>|<part2>|<taskId>#<payload>
        taskId , payload_str = text.split("|")[-1].split("#")
        logger.info(f"Received message - Task ID: {taskId} - Payload: {payload_str}")

        payload_data = json.loads(payload_str)
        params = payload_data.get("Params") or {}
        payload = BgTaskNotifyZalo(
            task_id=payload_data["TaskId"],
            action_type=payload_data["ActionType"],
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
        
        bot.send_message(phone_number=payload.phone_number, message=notify_message)
    except ValueError as e:
        logger.error(f"Invalid message format: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        bot.send_message(phone_number=payload.phone_number, message="Đã có lỗi trong trong quá trình xử lý xuất ảnh. Thử lại sau.")
        return
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        bot.send_message(phone_number=payload.phone_number, message="Đã có lỗi trong trong quá trình xử lý xuất ảnh. Thử lại sau.")
        return
    
    ch.basic_ack(delivery_tag=method.delivery_tag)
    logger.info("Sent notification successfully.")

def on_notify_otp(ch, method, properties, body, bot: IZaloBot = None, **kwargs):
    logger = kwargs.get("logger") or get_logger("MessageHandler")
    text = body.decode('utf-8')
    
    try:
        # Payload format: <part1>|<part2>|<taskId>#<payload>
        taskId , payload_str = text.split("|")[-1].split("#")
        logger.info(f"Received message - Task ID: {taskId} - Payload: {payload_str}")

        payload_data = json.loads(payload_str)
        params = payload_data.get("Params") or {}
        payload = BgTaskNotifyZalo(
            task_id=payload_data["TaskId"],
            action_type=payload_data["ActionType"],
            phone_number=payload_data["PhoneNumber"],
            message=payload_data["Message"],
            zip_file_url=payload_data["ZipFileUrl"],
            params=params
        )

        otp = params.get("otp")
        expire = params.get("expire")
        if not any([otp, expire]):
            raise ValueError("Missing OTP or expire time in the payload.")

        notify_message = payload.message.replace("<OTP>", otp).replace("<EXPIRE>", str(expire))

        if bot is None:
            logger.error("ZaloBot is None. Stop processing.")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return
        
        bot.send_message(phone_number=payload.phone_number, message=notify_message)
    except ValueError as e:
        logger.error(f"Invalid message format: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        bot.send_message(phone_number=payload.phone_number, message="Đã có lỗi trong quá trình gửi OTP. Thử lại sau.")
        return
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        bot.send_message(phone_number=payload.phone_number, message="Đã có lỗi trong quá trình gửi OTP. Thử lại sau.")
        return
    
    ch.basic_ack(delivery_tag=method.delivery_tag)
    logger.info("Sent notification successfully.")

# Task registry
TASK_REGISTRY: Dict[str, Callable] = {
    "DOWNLOAD_IMAGE": on_notify_download_image,
    "SEND_OTP": on_notify_otp
}