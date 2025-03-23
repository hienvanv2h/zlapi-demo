import pika
import os
import time
import threading
from models.logger import setup_logger

class RabbitMQ:
    def __init__(self):
        self.user = os.getenv('RABBITMQ_USER', 'guest')
        self.password = os.getenv('RABBITMQ_PASSWORD', 'guest')
        self.host = os.getenv('RABBITMQ_HOST', 'localhost')
        self.port = int(os.getenv('RABBITMQ_PORT', 5672))
        self.connection = None
        self.channel = None
        self.logger = setup_logger(name="RabbitMQ", log_file="rabbitmq.log")
        self.comsumer_thread = None

    def connect(self, retries=5, delay=2):
        for i in range(retries):
            try:
                credentials = pika.PlainCredentials(self.user, self.password)
                parameters = pika.ConnectionParameters(host=self.host, port=self.port, credentials=credentials)
                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()
                self.logger.info("Connected to RabbitMQ")
                return True
            except Exception as e:
                self.logger.warning(f"Failed to connect to RabbitMQ, retrying in {delay} seconds... ({i+1}/{retries})")
                time.sleep(delay)

        self.logger.error("Failed to connect to RabbitMQ after multiple retries.")
        return False

    def close(self):
        # Stop consuming
        if self.channel and self.channel.is_open:
            self.channel.stop_consuming()

        if self.connection and not self.connection.is_closed:
            self.connection.close()
            self.logger.info("RabbitMQ connection closed")

        if self.comsumer_thread and self.comsumer_thread.is_alive():
            self.comsumer_thread.join(timeout=3)
            self.logger.info("Consumer thread stopped")

    def consume(self, queue_name, callback):
        if not self.channel:
            self.logger.error("Connection is not established.")
            return False
        
        try:
            self.channel.queue_declare(queue=queue_name, durable=True)
            self.channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
            # Run in a separate thread
            def run_consumer():
                try:
                    self.channel.start_consuming()
                except pika.exceptions.StreamLostError as e:
                    self.logger.error(f"Stream connection lost: {e}")
                except Exception as e:
                    self.logger.error(f"Failed to setup consumer: {e}")
                finally:
                    self.logger.info("Consumer stopped.")

            self.comsumer_thread = threading.Thread(target=run_consumer, daemon=True)
            self.comsumer_thread.start()
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup consumer: {e}")
            return False

    def publish(self, queue_name, message):
        if not self.channel:
            self.logger.error("Connection is not established.")
            return False

        try:
            self.channel.queue_declare(queue=queue_name, durable=True)
            self.channel.basic_publish(exchange='',
                                    routing_key=queue_name,
                                    body=message,
                                    properties=pika.BasicProperties(
                                        delivery_mode=2,  # make message persistent
                                    ))
            self.logger.info(f"Sent message to queue {queue_name}: {message}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to publish message: {e}")
            return False