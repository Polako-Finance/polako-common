"""Contract validator for JSON Schema validation of messages."""

import json
import os
import uuid
from datetime import datetime

import jsonschema


class ContractValidator:
    """Validates messages against JSON Schema contracts."""

    def __init__(self, contracts_dir):
        """Initialize the ContractValidator.

        Args:
            contracts_dir (str): Path to the directory containing the contracts.
        """
        self.contracts_dir = contracts_dir
        self.schema_cache = {}

    def _load_schema(self, schema_file):
        """Load a schema from a file.

        Args:
            schema_file (str): Path to the schema file relative to the contracts directory.

        Returns:
            dict: The loaded schema.
        """
        schema_path = os.path.join(self.contracts_dir, schema_file)
        if schema_path in self.schema_cache:
            return self.schema_cache[schema_path]

        with open(schema_path, "r") as f:
            schema = json.load(f)
            self.schema_cache[schema_path] = schema
            return schema

    def _load_message_schema(self, domain, schema_file):
        """Load a message schema from a file.

        Args:
            domain (str): Domain of the message (e.g., 'mailing').
            schema_file (str): Name of the schema file.

        Returns:
            dict: The loaded schema.
        """
        schema_path = os.path.join(self.contracts_dir, domain, schema_file)
        if schema_path in self.schema_cache:
            return self.schema_cache[schema_path]

        with open(schema_path, "r") as f:
            schema = json.load(f)
            self.schema_cache[schema_path] = schema
            return schema

    def get_message_schema(self, domain, message_type):
        """Get the schema for a specific message type.

        Args:
            domain (str): Domain of the message (e.g., 'mailing').
            message_type (str): Type of the message.

        Returns:
            dict: The schema for the message type.

        Raises:
            ValueError: If the message type is not found.
        """
        # Try to load from individual schema file first (new format)
        try:
            schema = self._load_message_schema(domain, f"{message_type.lower()}.json")
            return schema
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        # Fall back to legacy format with all message types in one file
        try:
            schema = self._load_message_schema(domain, "email_messages.json")
            if message_type in schema.get("definitions", {}):
                return schema["definitions"][message_type]
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        raise ValueError(f"Message type '{message_type}' not found in domain '{domain}'")

    def validate_message(self, domain, message_type, message_data):
        """Validate a message against its schema.

        Args:
            domain (str): Domain of the message (e.g., 'mailing').
            message_type (str): Type of the message.
            message_data (dict): Message data to validate.

        Raises:
            jsonschema.exceptions.ValidationError: If the message is invalid.
        """
        schema = self.get_message_schema(domain, message_type)
        jsonschema.validate(instance=message_data, schema=schema)

    def create_envelope(self, message_type, data, correlation_id=None, causation_id=None, sender=None):
        """Create a message envelope.

        Args:
            message_type (str): Type of the message.
            data (dict): Message data.
            correlation_id (str, optional): Correlation ID. Defaults to None.
            causation_id (str, optional): Causation ID. Defaults to None.
            sender (str, optional): Sender service name. Defaults to None.

        Returns:
            dict: The message envelope.
        """
        envelope = {
            "metadata": {
                "messageId": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "messageType": message_type,
                "data": data,
                "version": "1.0"
            }
        }

        if correlation_id:
            envelope["metadata"]["correlationId"] = correlation_id
        if causation_id:
            envelope["metadata"]["causationId"] = causation_id
        if sender:
            envelope["metadata"]["sender"] = sender

        # Validate the envelope against the envelope schema
        envelope_schema = self._load_schema("envelope.json")
        jsonschema.validate(instance=envelope, schema=envelope_schema)

        return envelope
