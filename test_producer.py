import time
from models.rabbitmq import RabbitMQ

def publish_message():
    rabbitmq = RabbitMQ()
    try:
        rabbitmq.connect()
        for i in range(50):
            rabbitmq.publish_to_queue(queue_name="XXX_QUEUE", message=f"({i}) Hello, RabbitMQ!")
            time.sleep(2)
        print("Messages published successfully.")
    except Exception as e:
        print(f"Failed to publish message: {e}")
    finally:
        rabbitmq.close()

publish_message()