import pika
import os
import time
import threading
import pika.exceptions
import pika.spec

from interfaces import IZaloBot
from utils.logger import setup_logger

class RabbitMQ:
    def __init__(self, bot: IZaloBot = None):
        self.user = os.getenv('RABBITMQ_USER', 'guest')
        self.password = os.getenv('RABBITMQ_PASSWORD', 'guest')
        self.host = os.getenv('RABBITMQ_HOST', 'localhost')
        self.port = int(os.getenv('RABBITMQ_PORT', 5672))
        self.connection = None
        self.channel = None
        self.logger = setup_logger(name="RabbitMQ", log_file="rabbitmq.log")
        self.consumer_thread = None
        self.is_consuming = False
        self.zalo_bot = bot

    def connect(self, retries=5, delay=2):
        for i in range(retries):
            try:
                credentials = pika.PlainCredentials(self.user, self.password)
                parameters = pika.ConnectionParameters(host=self.host, port=self.port, credentials=credentials)
                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()
                self.logger.info("============================================================================")
                self.logger.info("Connected to RabbitMQ")
                return True
            except Exception as e:
                self.logger.warning(f"Failed to connect to RabbitMQ, retrying in {delay} seconds... ({i+1}/{retries})")
                time.sleep(delay)

        self.logger.error("Failed to connect to RabbitMQ after multiple retries.")
        return False

    def close(self):
        self.is_consuming = False
        try:
            # Stop consuming
            if self.channel and self.channel.is_open:
                self.channel.stop_consuming()
            
            if self.consumer_thread and self.consumer_thread.is_alive():
                self.consumer_thread.join(timeout=3)
                self.logger.info("Consumer thread stopped")

            if self.connection and not self.connection.is_closed:
                self.connection.close()
                self.logger.info("RabbitMQ connection closed.")
        except Exception as e:
            self.logger.error(f"Failed to close RabbitMQ connection: {e}")

    def declare_exchange(self, exchange_name, exchange_type='direct', passive=False, durable=True, auto_delete=False):
        """
        Declare an exchange with specified parameters
        
        Parameters:
        - exchange_name: Name of the exchange
        - exchange_type: Type of exchange ('direct', 'fanout', 'topic', 'headers')
        - durable: Whether the exchange should survive broker restarts
        - passive: Whether the exchange already exists
        - auto_delete: Whether the exchange should be deleted when no longer used
        """
        if not self.channel:
            self.logger.error("Connection is not established.")
            return False

        try:
            self.channel.exchange_declare(
                exchange=exchange_name, 
                exchange_type=exchange_type, 
                passive=passive,
                durable=durable,
                auto_delete=auto_delete
            )
            self.logger.info(f"Declared exchange: {exchange_name} ({exchange_type.upper()})")
            return True
        except Exception as e:
            self.logger.error(f"Failed to declare exchange: {e}")
            return False
    
    def declare_queue(self, queue_name, passive=False, durable=False, exclusive=False, auto_delete=False):
        """
        Declare a queue with specified parameters

        Parameters:
        - queue_name: Name of the queue
        - passive: Whether the queue already exists
        - durable: Whether the queue should survive broker restarts
        - exclusive: Whether the queue should be exclusive to this connection
        - auto_delete: Whether the queue should be deleted when no longer used

        Returns:
        - queue_name: Name of the declared queue
        """
        if not self.channel:
            self.logger.error("Connection is not established.")
            return False

        try:
            result = self.channel.queue_declare(
                queue=queue_name, 
                passive=passive, 
                durable=durable, 
                exclusive=exclusive, 
                auto_delete=auto_delete
            )
            self.logger.info(f"Declared queue: {queue_name}")
            return result.method.queue
        except Exception as e:
            self.logger.error(f"Failed to declare queue: {e}")
            return False

    def bind_queue(self, queue_name, exchange_name, routing_key='', args: dict|None = None):
        """
        Bind a queue to an exchange with a routing key

        Parameters:
        - queue_name: Name of the queue
        - exchange_name: Name of the exchange
        - routing_key: Routing key for the binding (for direct & topic exchanges)
        """
        if not self.channel:
            self.logger.error("Connection is not established.")
            return False

        try:
            self.channel.queue_bind(queue=queue_name, exchange=exchange_name, routing_key=routing_key, arguments=args)
            self.logger.info(f"Bound queue: {queue_name} to exchange {exchange_name} with routing key {routing_key}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to bind queue: {e}")
            return False

    def consume(self, queue_name, callback, auto_ack=False):
        """
        Consume messages from a queue

        Parameters:
        - queue_name: Name of the queue
        - callback: Callback function to handle received messages
        - auto_ack: Whether to automatically acknowledge received messages
        """
        if not self.channel:
            self.logger.error("Connection is not established.")
            return False
        
        def wrapper_callback(ch, method, properties, body):
            # Truyền thêm logger vào callback
            callback(ch, method, properties, body, logger=self.logger, bot=self.zalo_bot)
        
        try:
            self.channel.queue_declare(queue=queue_name, durable=True)   # use existing or create
            self.channel.basic_consume(queue=queue_name, on_message_callback=wrapper_callback, auto_ack=auto_ack)

            # Run in a separate thread
            def run_consumer():
                self.is_consuming = True
                try:
                    while self.is_consuming:
                        try:
                            self.channel.start_consuming()
                        except pika.exceptions.StreamLostError as e:
                            if self.is_consuming:
                                self.logger.error(f"Stream connection lost: {e}.\nAttempting to reconnect...")
                                if self.reconnect():
                                    self.channel.queue_declare(queue=queue_name, durable=True)
                                    self.channel.basic_consume(queue=queue_name, on_message_callback=wrapper_callback, auto_ack=auto_ack)
                                else:
                                    self.logger.error("Failed to reconnect to RabbitMQ. Stopping consumer.")
                                    break
                        except pika.exceptions.ChannelClosedByBroker as e:
                            if self.is_consuming:
                                self.logger.error(f"Channel closed by broker: {e}.\nAttempting to reconnect...")
                                if self.reconnect():
                                    self.channel.queue_declare(queue=queue_name, durable=True)
                                    self.channel.basic_consume(queue=queue_name, on_message_callback=wrapper_callback, auto_ack=auto_ack)
                                else:
                                    self.logger.error("Failed to reconnect to RabbitMQ. Stopping consumer.")
                                    break
                except Exception as e:
                    self.logger.error(f"Failed to setup consumer: {e}")
                finally:
                    self.logger.info("Consumer stopped.")

            self.consumer_thread = threading.Thread(target=run_consumer, daemon=True)
            self.consumer_thread.start()
            self.logger.info(f"Consumer started for queue: {queue_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup consumer: {e}")
            return False
    
    def consume2(self, queue_name, callback_registry, auto_ack=False):
        """
        Consume messages from a queue

        Parameters:
        - queue_name: Name of the queue
        - callback: Callback function to handle received messages
        - auto_ack: Whether to automatically acknowledge received messages
        """
        if not self.channel:
            self.logger.error("Connection is not established.")
            return False
        
        def wrapper_callback(ch, method, properties, body):
            """Xử lý message và gọi callback tương ứng"""
            message = body.decode('utf-8')
            # Payload format: <_>|<actioType>|<taskId>#<payload>
            data_fragment = message.split("|")
            action_type = data_fragment[1]

            callback = callback_registry.get(action_type)
            if not callback:
                self.logger.warning(f"No handler found for action_type: {action_type}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return
            
            # Truyền thêm logger vào callback
            callback(ch, method, properties, body, bot=self.zalo_bot, logger=self.logger)
        
        try:
            self.channel.queue_declare(queue=queue_name, durable=True)   # use existing or create
            self.channel.basic_consume(queue=queue_name, on_message_callback=wrapper_callback, auto_ack=auto_ack)

            # Run in a separate thread
            def run_consumer():
                self.is_consuming = True
                try:
                    while self.is_consuming:
                        try:
                            self.channel.start_consuming()
                        except pika.exceptions.StreamLostError as e:
                            if self.is_consuming:
                                self.logger.error(f"Stream connection lost: {e}.\nAttempting to reconnect...")
                                if self.reconnect():
                                    self.channel.queue_declare(queue=queue_name, durable=True)
                                    self.channel.basic_consume(queue=queue_name, on_message_callback=wrapper_callback, auto_ack=auto_ack)
                                else:
                                    self.logger.error("Failed to reconnect to RabbitMQ. Stopping consumer.")
                                    break
                        except pika.exceptions.ChannelClosedByBroker as e:
                            if self.is_consuming:
                                self.logger.error(f"Channel closed by broker: {e}.\nAttempting to reconnect...")
                                if self.reconnect():
                                    self.channel.queue_declare(queue=queue_name, durable=True)
                                    self.channel.basic_consume(queue=queue_name, on_message_callback=wrapper_callback, auto_ack=auto_ack)
                                else:
                                    self.logger.error("Failed to reconnect to RabbitMQ. Stopping consumer.")
                                    break
                except Exception as e:
                    self.logger.error(f"Failed to setup consumer: {e}")
                finally:
                    self.logger.info("Consumer stopped.")

            self.consumer_thread = threading.Thread(target=run_consumer, daemon=True)
            self.consumer_thread.start()
            self.logger.info(f"Consumer started for queue: {queue_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup consumer: {e}")
            return False
    
    def reconnect(self):
        """Reconnect to RabbitMQ"""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            
            return self.connect()
        except Exception as e:
            self.logger.error(f"Error while reconnecting: {e}")
            return False

    def publish(self, message, exchange='', routing_key='', properties: pika.spec.BasicProperties|None=None):
        """
        Publish a message to an exchange with a routing key

        Parameters:
        - message: Message body to be published
        - exchange: Name of the exchange
        - routing_key: Routing key for the message
        - properties: Additional properties for the message
        """
        if not self.channel:
            self.logger.error("Connection is not established.")
            return False

        try:
            if properties is None:
                properties = pika.BasicProperties(delivery_mode=2) # make message persistent

            self.channel.basic_publish(exchange=exchange, routing_key=routing_key, body=message, properties=properties)
            
            self.logger.info(f"Published message to exchange {exchange} with routing key {routing_key}")
            self.logger.debug(f"Message: {message}")
            return True
        except pika.exceptions.ChannelClosedByBroker as e:
            self.logger.error(f"Channel closed by broker while publishing: {e}.\nAttempting to reconnect...")
            if self.reconnect():
                return self.publish(message, exchange, routing_key, properties)
            return False
        except Exception as e:
            self.logger.error(f"Failed to publish message: {e}")
            return False
    
    def publish_to_queue(self, message, queue_name):
        """
        Directly publish a message to a queue (using default exchange)

        Parameters:
        - message: Message body to be published
        - queue_name: Name of the queue
        """
        self.declare_queue(queue_name, durable=True)
        return self.publish(message=message, exchange='', routing_key=queue_name)