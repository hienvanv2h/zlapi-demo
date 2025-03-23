from models.rabbitmq import RabbitMQ

def publish_message():
    rabbitmq = RabbitMQ()
    try:
        rabbitmq.connect()
        rabbitmq.publish("test-queue", "Hello, RabbitMQ!")
        print("Message published successfully.")
    except Exception as e:
        print(f"Failed to publish message: {e}")
    finally:
        rabbitmq.close()

publish_message()