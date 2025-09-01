"""Tests for the ContractValidator class."""

import json
import os
import unittest
from unittest.mock import patch, mock_open

from polako_common.messaging.contract_validator import ContractValidator


class TestContractValidator(unittest.TestCase):
    """Test case for the ContractValidator class."""

    def setUp(self):
        """Set up the test case."""
        # Mock the contracts directory
        self.contracts_dir = "/mock/contracts"
        
        # Mock envelope schema
        self.envelope_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "Message Envelope",
            "type": "object",
            "required": ["metadata"],
            "properties": {
                "metadata": {
                    "type": "object",
                    "required": ["messageId", "timestamp", "messageType", "data"],
                    "properties": {
                        "messageId": {"type": "string", "format": "uuid"},
                        "timestamp": {"type": "string", "format": "date-time"},
                        "correlationId": {"type": "string", "format": "uuid"},
                        "causationId": {"type": "string", "format": "uuid"},
                        "sender": {"type": "string"},
                        "version": {"type": "string"},
                        "messageType": {"type": "string"},
                        "data": {"type": "object"}
                    }
                }
            }
        }
        
        # Mock email message schema
        self.email_message_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "Email Message Contracts",
            "description": "Contracts for all email message types in the Polako Finance system",
            "definitions": {
                "SuccessEmail": {
                    "type": "object",
                    "required": ["recipientName", "transactionId", "amount", "currency", "merchantName"],
                    "properties": {
                        "recipientName": {"type": "string"},
                        "transactionId": {"type": "string"},
                        "amount": {"type": "number"},
                        "currency": {"type": "string"},
                        "merchantName": {"type": "string"}
                    }
                }
            }
        }
        
        # Create a patcher for the open function
        self.open_patcher = patch("builtins.open", mock_open())
        self.mock_open = self.open_patcher.start()
        
        # Create a patcher for the os.path.join function
        self.join_patcher = patch("os.path.join")
        self.mock_join = self.join_patcher.start()
        
        # Configure the mock_join to return specific paths
        def mock_join_side_effect(*args):
            if args[1] == "envelope.json":
                return "/mock/contracts/envelope.json"
            elif args[1] == "mailing" and args[2] == "email_messages.json":
                return "/mock/contracts/mailing/email_messages.json"
            return os.path.join(*args)
        
        self.mock_join.side_effect = mock_join_side_effect
        
        # Create a patcher for json.load
        self.json_load_patcher = patch("json.load")
        self.mock_json_load = self.json_load_patcher.start()
        
        # Configure the mock_json_load to return specific schemas
        def mock_json_load_side_effect(file_obj):
            if str(file_obj) == "<mock open file '/mock/contracts/envelope.json'>":
                return self.envelope_schema
            elif str(file_obj) == "<mock open file '/mock/contracts/mailing/email_messages.json'>":
                return self.email_message_schema
            return {}
        
        self.mock_json_load.side_effect = mock_json_load_side_effect
        
        # Create the ContractValidator instance
        self.validator = ContractValidator(self.contracts_dir)
    
    def tearDown(self):
        """Tear down the test case."""
        self.open_patcher.stop()
        self.join_patcher.stop()
        self.json_load_patcher.stop()
    
    def test_load_schema(self):
        """Test loading a schema."""
        schema = self.validator._load_schema("envelope.json")
        self.assertEqual(schema, self.envelope_schema)
        self.mock_open.assert_called_with("/mock/contracts/envelope.json", "r")
    
    def test_load_message_schema(self):
        """Test loading a message schema."""
        schema = self.validator._load_message_schema("mailing", "email_messages.json")
        self.assertEqual(schema, self.email_message_schema)
        self.mock_open.assert_called_with("/mock/contracts/mailing/email_messages.json", "r")
    
    def test_get_message_schema(self):
        """Test getting a message schema."""
        schema = self.validator.get_message_schema("mailing", "SuccessEmail")
        self.assertEqual(schema, self.email_message_schema["definitions"]["SuccessEmail"])
    
    def test_get_message_schema_not_found(self):
        """Test getting a message schema that doesn't exist."""
        with self.assertRaises(ValueError):
            self.validator.get_message_schema("mailing", "NonExistentType")
    
    @patch("jsonschema.validate")
    def test_validate_message(self, mock_validate):
        """Test validating a message."""
        message_data = {
            "recipientName": "John Doe",
            "transactionId": "123456",
            "amount": 100.0,
            "currency": "USD",
            "merchantName": "Test Merchant"
        }
        self.validator.validate_message("mailing", "SuccessEmail", message_data)
        mock_validate.assert_called_once()
    
    @patch("jsonschema.validate")
    def test_create_envelope(self, mock_validate):
        """Test creating an envelope."""
        message_data = {"test": "data"}
        envelope = self.validator.create_envelope(
            message_type="TestType",
            data=message_data,
            correlation_id="corr-123",
            causation_id="cause-456",
            sender="test-service"
        )
        
        self.assertIn("metadata", envelope)
        self.assertIn("messageId", envelope["metadata"])
        self.assertIn("timestamp", envelope["metadata"])
        self.assertEqual(envelope["metadata"]["messageType"], "TestType")
        self.assertEqual(envelope["metadata"]["data"], message_data)
        self.assertEqual(envelope["metadata"]["correlationId"], "corr-123")
        self.assertEqual(envelope["metadata"]["causationId"], "cause-456")
        self.assertEqual(envelope["metadata"]["sender"], "test-service")
        self.assertEqual(envelope["metadata"]["version"], "1.0")
        
        mock_validate.assert_called_once()


if __name__ == "__main__":
    unittest.main()
