"""RabbitMQ client for handling messages with simple JSON serialization."""

import asyncio
import json
import logging
from typing import Callable, Dict, Any, Optional

import aio_pika
from aio_pika import Message, ExchangeType, connect_robust
from aio_pika.abc import AbstractIncomingMessage

logger = logging.getLogger(__name__)


class RabbitMQClient:
    """RabbitMQ client for handling messages with simple JSON serialization."""

    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        vhost: str,
        exchange_name: str,
        queue_name: Optional[str] = None,
        routing_key: Optional[str] = None,
        service_name: Optional[str] = None,
        contracts_dir: Optional[str] = None,
    ):
        """Initialize RabbitMQ client.
        
        Args:
            host: RabbitMQ host
            port: RabbitMQ port
            user: RabbitMQ username
            password: RabbitMQ password
            vhost: RabbitMQ virtual host
            exchange_name: Exchange name
            queue_name: Queue name (optional)
            routing_key: Routing key (optional)
            service_name: Name of the service using this client (optional)
            contracts_dir: Directory containing contract schemas (optional)
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.vhost = vhost
        self.exchange_name = exchange_name
        self.queue_name = queue_name
        self.routing_key = routing_key
        self.service_name = service_name
        
        self.connection = None
        self.channel = None
        self.exchange = None
        self.queue = None
        self.message_handlers: Dict[str, Callable] = {}
        self._is_connected = False

    async def connect(self) -> None:
        """Connect to RabbitMQ server."""
        try:
            # Connect to RabbitMQ
            self.connection = await connect_robust(
                host=self.host,
                port=self.port,
                login=self.user,
                password=self.password,
                virtualhost=self.vhost,
            )
            
            # Create channel
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)
            
            # Declare exchange
            self.exchange = await self.channel.declare_exchange(
                self.exchange_name,
                ExchangeType.TOPIC,
                durable=True,
            )
            
            # Declare queue if queue_name is provided
            if self.queue_name:
                self.queue = await self.channel.declare_queue(
                    self.queue_name,
                    arguments={"x-queue-type": "quorum"},
                    durable=True,
                    auto_delete=False,
                )
                
                # Bind queue to exchange with routing key if provided
                if self.routing_key:
                    await self.queue.bind(
                        exchange=self.exchange,
                        routing_key=self.routing_key,
                    )
            
            self._is_connected = True
            logger.info("Connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            self._is_connected = False
            raise

    async def disconnect(self) -> None:
        """Disconnect from RabbitMQ server."""
        if self.connection:
            await self.connection.close()
            self._is_connected = False
            logger.info("Disconnected from RabbitMQ")

    def register_handler(self, message_type: str, handler: Callable) -> None:
        """Register a handler for a specific message type.
        
        Args:
            message_type: Type of message to handle
            handler: Handler function
        """
        self.message_handlers[message_type] = handler
        logger.info(f"Registered handler for message type: {message_type}")

    async def _process_message(self, message: AbstractIncomingMessage) -> None:
        """Process incoming message.
        
        Args:
            message: Incoming message
        """
        async with message.process():
            try:
                # Decode message body
                body = message.body.decode()
                envelope = json.loads(body)
                
                # Extract message metadata
                if "metadata" not in envelope:
                    logger.error(f"Message has no metadata: {body}")
                    return
                    
                metadata = envelope.get("metadata", {})
                message_type = metadata.get("messageType")
                if not message_type:
                    logger.error(f"Message has no messageType: {body}")
                    return
                
                # Find handler for message type
                handler = self.message_handlers.get(message_type)
                if not handler:
                    logger.warning(f"No handler registered for message type: {message_type}")
                    return
                
                # Extract message data from envelope
                payload = envelope.get("payload")
                if payload is None:
                    logger.error(f"Message has no payload: {body}")
                    return
                
                # Call handler with message payload
                await handler(payload)
                logger.info(f"Processed message of type: {message_type}")
            except json.JSONDecodeError:
                logger.error(f"Failed to decode message: {message.body}")
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")

    async def start_consuming(self) -> None:
        """Start consuming messages from the queue."""
        if not self._is_connected:
            await self.connect()
        
        if not self.queue:
            raise ValueError("Queue is not declared. Cannot start consuming.")
        
        await self.queue.consume(self._process_message)
        logger.info(f"Started consuming messages from queue: {self.queue_name}")

    async def publish_message(
        self, 
        routing_key: str, 
        envelope: Dict[str, Any]
    ) -> None:
        """Publish a pre-created envelope to the exchange.
        
        Args:
            routing_key: Routing key for the message
            envelope: Pre-created message envelope (should be created using contract library)
        """
        if not self._is_connected:
            await self.connect()
        
        # Create message
        message = Message(
            body=json.dumps(envelope).encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        
        # Publish message
        await self.exchange.publish(
            message=message,
            routing_key=routing_key,
        )
        logger.info(f"Published message with routing key: {routing_key}")
