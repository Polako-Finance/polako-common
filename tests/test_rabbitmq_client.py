"""Tests for the RabbitMQClient class."""

import asyncio
import json
import unittest
from unittest.mock import patch, MagicMock, AsyncMock

from polako_common.messaging.rabbitmq_client import RabbitMQClient
from polako_common.messaging.contract_validator import ContractValidator


class TestRabbitMQClient(unittest.TestCase):
    """Test case for the RabbitMQClient class."""

    def setUp(self):
        """Set up the test case."""
        # Create mock for ContractValidator
        self.mock_validator = MagicMock(spec=ContractValidator)
        
        # Configure the mock validator
        self.mock_validator.create_envelope.return_value = {
            "metadata": {
                "messageId": "test-id",
                "timestamp": "2023-01-01T00:00:00Z",
                "messageType": "TestType",
                "data": {"test": "data"}
            }
        }
        
        # Create patches
        self.validator_patcher = patch('polako_common.messaging.rabbitmq_client.ContractValidator', 
                                      return_value=self.mock_validator)
        self.connect_robust_patcher = patch('polako_common.messaging.rabbitmq_client.connect_robust', 
                                           new_callable=AsyncMock)
        
        # Start patches
        self.mock_validator_class = self.validator_patcher.start()
        self.mock_connect_robust = self.connect_robust_patcher.start()
        
        # Configure mock connection and channel
        self.mock_connection = AsyncMock()
        self.mock_channel = AsyncMock()
        self.mock_exchange = AsyncMock()
        self.mock_queue = AsyncMock()
        
        self.mock_connect_robust.return_value = self.mock_connection
        self.mock_connection.channel.return_value = self.mock_channel
        self.mock_channel.declare_exchange.return_value = self.mock_exchange
        self.mock_channel.declare_queue.return_value = self.mock_queue
        
        # Create RabbitMQClient instance
        self.client = RabbitMQClient(
            host="localhost",
            port=5672,
            user="guest",
            password="guest",
            vhost="/",
            exchange_name="test_exchange",
            queue_name="test_queue",
            routing_key="test.key",
            service_name="test-service",
            contracts_dir="/test/contracts"
        )
    
    def tearDown(self):
        """Tear down the test case."""
        self.validator_patcher.stop()
        self.connect_robust_patcher.stop()
    
    def test_init(self):
        """Test initialization."""
        self.assertEqual(self.client.host, "localhost")
        self.assertEqual(self.client.port, 5672)
        self.assertEqual(self.client.user, "guest")
        self.assertEqual(self.client.password, "guest")
        self.assertEqual(self.client.vhost, "/")
        self.assertEqual(self.client.exchange_name, "test_exchange")
        self.assertEqual(self.client.queue_name, "test_queue")
        self.assertEqual(self.client.routing_key, "test.key")
        self.assertEqual(self.client.service_name, "test-service")
        
        self.mock_validator_class.assert_called_once_with("/test/contracts")
    
    async def async_test(self, coroutine):
        """Run an async test."""
        return await coroutine
    
    def test_connect(self):
        """Test connect method."""
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.async_test(self.client.connect()))
        
        self.mock_connect_robust.assert_called_once_with(
            host="localhost",
            port=5672,
            login="guest",
            password="guest",
            virtualhost="/"
        )
        self.mock_connection.channel.assert_called_once()
        self.mock_channel.set_qos.assert_called_once_with(prefetch_count=10)
        self.mock_channel.declare_exchange.assert_called_once()
        self.mock_channel.declare_queue.assert_called_once()
        self.mock_queue.bind.assert_called_once_with(
            exchange=self.mock_exchange,
            routing_key="test.key"
        )
        self.assertTrue(self.client._is_connected)
    
    def test_disconnect(self):
        """Test disconnect method."""
        self.client.connection = self.mock_connection
        
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.async_test(self.client.disconnect()))
        
        self.mock_connection.close.assert_called_once()
        self.assertFalse(self.client._is_connected)
    
    def test_register_handler(self):
        """Test register_handler method."""
        handler = MagicMock()
        self.client.register_handler("test_type", handler)
        
        self.assertIn("test_type", self.client.message_handlers)
        self.assertEqual(self.client.message_handlers["test_type"], handler)
    
    def test_publish_message(self):
        """Test publish_message method."""
        message_data = {"test": "data"}
        
        # Set up the client to be connected
        self.client._is_connected = True
        self.client.exchange = self.mock_exchange
        
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.async_test(
            self.client.publish_message(
                routing_key="test.route",
                message_data=message_data,
                message_type="TestType",
                correlation_id="corr-123",
                causation_id="cause-456"
            )
        ))
        
        # Check that the validator was called
        self.mock_validator.validate_message.assert_called_once_with(
            "test", "TestType", message_data
        )
        
        # Check that the envelope was created
        self.mock_validator.create_envelope.assert_called_once_with(
            message_type="TestType",
            data=message_data,
            correlation_id="corr-123",
            causation_id="cause-456",
            sender="test-service"
        )
        
        # Check that the message was published
        self.mock_exchange.publish.assert_called_once()
        
    async def test_process_message(self):
        """Test _process_message method."""
        # Create a mock message
        mock_message = AsyncMock()
        mock_message.body.decode.return_value = json.dumps({
            "metadata": {
                "messageType": "test_type",
                "data": {"test": "data"}
            }
        })
        
        # Create a mock handler
        mock_handler = AsyncMock()
        self.client.message_handlers["test_type"] = mock_handler
        self.client.service_name = "test-service"
        
        # Process the message
        await self.client._process_message(mock_message)
        
        # Check that the message was processed
        mock_message.process.assert_called_once()
        mock_handler.assert_called_once_with({"test": "data"})
        
        # Check that validation was attempted
        self.mock_validator.validate_message.assert_called_once_with(
            "test", "test_type", {"test": "data"}
        )


if __name__ == "__main__":
    unittest.main()
